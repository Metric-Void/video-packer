# !/usr/bin/env python
# -*- coding:utf-8 -*-

from PyQt5.QtWidgets import QMessageBox, QLineEdit
from PyQt5.QtGui import QIcon

import sys
import os


class QFileEdit(QLineEdit):
    def __init__(self, parent):
        super(QFileEdit, self).__init__(parent)

        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            filepath = str(urls[0].path())[1:]
            self.setText(filepath)