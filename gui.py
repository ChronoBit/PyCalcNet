import asyncio
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget, QPushButton, QLineEdit
from net.net_client import NetClient
from to_client.calc_response import CalcResponse
from to_server.alive_tick import AliveTick
from to_server.calc_request import CalcRequest

import loader

loader.load_all_modules_from_dir('to_client')
loader.load_all_modules_from_dir('to_server')


class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Calculator')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)
        self.setGeometry(0, 0, 250, 350)
        self._to_center()
        self.adjustSize()

        self.operations = []
        self.is_send = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QGridLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        central_widget.setLayout(self.layout)

        self.text = QLineEdit()
        self.text.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.text.setReadOnly(True)
        self.text.setStyleSheet('font-size: 20px; padding: 5px')
        self.layout.addWidget(self.text, 0, 0, 1, 4)

        self._number_btn('7', 1, 0)
        self._number_btn('8', 1, 1)
        self._number_btn('9', 1, 2)
        self._op_btn('/', 1, 3)

        self._number_btn('4', 2, 0)
        self._number_btn('5', 2, 1)
        self._number_btn('6', 2, 2)
        self._op_btn('*', 2, 3)

        self._number_btn('1', 3, 0)
        self._number_btn('2', 3, 1)
        self._number_btn('3', 3, 2)
        self._op_btn('-', 3, 3)

        self._number_btn('0', 4, 0)
        self._number_btn('.', 4, 1)
        self.result_btn = self._btn('=', 4, 2)
        self.result_btn.setDisabled(True)
        self.result_btn.clicked.connect(self._on_result)
        self._op_btn('+', 4, 3)

        self._btn('C', 5, 0, 2).clicked.connect(self.clear)
        self._btn('Del', 5, 2, 2).clicked.connect(self.delete)

        CalcResponse.parse = lambda packet: self._result(packet.result)

        self.tcp = NetClient('127.0.0.1', 1000)
        self.tcp.tcp.on_connected = self._connection_changed
        asyncio.create_task(self.tcp.run())
        asyncio.create_task(self.alive_tick())

        self.keys = {
            '1': lambda: self.number('1'),
            '2': lambda: self.number('2'),
            '3': lambda: self.number('3'),
            '4': lambda: self.number('4'),
            '5': lambda: self.number('5'),
            '6': lambda: self.number('6'),
            '7': lambda: self.number('7'),
            '8': lambda: self.number('8'),
            '9': lambda: self.number('9'),
            '0': lambda: self.number('0'),
            '.': lambda: self.number('.'),

            '+': lambda: self.operator('+'),
            '-': lambda: self.operator('-'),
            '*': lambda: self.operator('*'),
            '/': lambda: self.operator('/'),

            '=': lambda: self._on_result(),
        }

        backspace_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Backspace), self)
        delete_shortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Delete), self)
        backspace_shortcut.activated.connect(self.delete)
        delete_shortcut.activated.connect(self.delete)

        self.refresh()

    async def alive_tick(self):
        await asyncio.sleep(5)
        if self.tcp.tcp.is_connected():
            tick = AliveTick()
            await self.tcp.send(tick)
        asyncio.create_task(self.alive_tick())

    def _connection_changed(self, val):
        self.result_btn.setDisabled(not val)
        if not val:
            self.is_send = False

    def _result(self, result):
        self.operations.clear()
        if result < 0:
            result *= -1
            self.operations.append('-')
        self.operations.append('{:.02f}'.format(result))
        self.refresh()
        self.is_send = False

    def refresh(self):
        if len(self.operations) == 0:
            self.text.setText('0')
            return
        self.text.setText(''.join(self.operations))

    def clear(self):
        if self.is_send:
            return
        self.operations.clear()
        self.refresh()

    def delete(self):
        if self.is_send or len(self.operations) == 0:
            return
        last = self.operations[-1]
        last = last[:-1]
        if len(last) == 0:
            del self.operations[-1]
        else:
            self.operations[-1] = last
        self.refresh()

    def number(self, num: str):
        if self.is_send:
            return
        if not num.isdigit() and not num == '.':
            return
        if len(self.operations) == 0:
            if num == '0':
                return
            if num == '.':
                self.operations.append('0.')
            else:
                self.operations.append(num)
        else:
            if self.operations[-1] in ['+', '-', '*', '/']:
                if num == '0':
                    return
                if num == '.':
                    self.operations.append('0.')
                else:
                    self.operations.append(num)
            else:
                last = self.operations[-1]
                if num == '.' and '.' in last:
                    return
                if num == '0' and last[0] == '0':
                    return
                self.operations[-1] += num
        self.refresh()

    def operator(self, op):
        if self.is_send:
            return
        if op not in ['+', '-', '*', '/']:
            return
        if len(self.operations) == 0:
            if op == '-':
                self.operations.append('-')
                self.refresh()
                return
            return
        last = self.operations[-1]
        if last[-1] == '.':
            self.operations[-1] = last[:-1]
        elif last in ['+', '-', '*', '/']:
            return
        self.operations.append(op)
        self.refresh()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        key = e.key()
        text = e.text()
        if key == Qt.Key.Key_Backspace:
            self.delete()
        elif key in [Qt.Key.Key_Enter, 0x1000004]:
            self._on_result()
        elif text in self.keys:
            self.keys[text]()

    def _btn(self, text, x, y, row=1):
        btn = QPushButton(text)
        btn.setStyleSheet('font-size: 20px; padding: 10px 20px')
        self.layout.addWidget(btn, x, y, 1, row)
        return btn

    def _number_btn(self, text, x, y, row=1):
        btn = self._btn(text, x, y, row)
        btn.clicked.connect(lambda: self._on_number_click(text))

    def _op_btn(self, text, x, y, row=1):
        btn = self._btn(text, x, y, row)
        btn.clicked.connect(lambda: self._on_op_click(text))

    def _to_center(self):
        rect = self.frameGeometry()
        center = QApplication.primaryScreen().availableGeometry().center()
        rect.moveCenter(center)
        self.move(rect.topLeft())

    def _on_number_click(self, val):
        self.number(val)

    def _on_op_click(self, val):
        self.operator(val)

    def _on_result(self):
        if self.is_send or not self.tcp.tcp.is_connected() or len(self.operations) < 2:
            return
        last = self.operations[-1]
        if last[-1] == '.':
            self.operations[-1] = last[:-1]
        elif last in ['+', '-', '*', '/']:
            del self.operations[-1]
        self.is_send = True
        req = CalcRequest()
        req.operations = self.operations[:]
        if req.operations[0] == '-':
            req.operations.insert(0, '0')
        asyncio.create_task(self.tcp.send(req))
