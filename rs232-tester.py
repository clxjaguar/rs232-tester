#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://github.com/clxjaguar/rs232-tester

import sys, serial, serial.tools.list_ports

try:
	# sudo apt-get install python3-pyqt5
	from PyQt5.QtGui import *
	from PyQt5.QtCore import *
	from PyQt5.QtWidgets import *
except:
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *


class GUI(QWidget):
	def __init__(self):
		QWidget.__init__(self)
		self.msg = bytes([0x55])
		self.initUI()
		self.refreshSerial()

	def initUI(self):
		self.setStyleSheet("\
			QLabel { margin: 0px; padding: 0px; } \
			QLabel#top_padding { font-size: 8px; } \
			QPushButton::checked#green { color: #000000; background: #00ff00; } \
			QSplitter::handle:vertical   { image: none; } \
			QSplitter::handle:horizontal { width:  2px; image: none; } \
			QGroupBox { border: 1px solid #707070; border-radius: 50px; padding: 0px; } \
		");

		def mkQLabel(text=None, layout=None, alignment=Qt.AlignLeft, objectName=None):
			o = QLabel()
			if objectName:
				o.setObjectName(objectName)
			o.setAlignment(alignment)
			if text:
				o.setText(text)
			if type(layout) == QGridLayout:
				layout.addWidget(o, gridPlacement[0], gridPlacement[1], gridSpan[0], gridSpan[1])
			elif layout != None:
				layout.addWidget(o)
			return o

		def mkButton(text, layout=None, function=None, gridPlacement=(0,0), gridSpan=(1,1), setCheckable=False, toolButton=False, objectName=None, enabled=True):
			if not toolButton:
				btn = QPushButton(text)
			else:
				btn = QToolButton()
				btn.setText(text)
			btn.setCheckable(setCheckable)
			if objectName:
				btn.setObjectName(objectName)
			btn.setFocusPolicy(Qt.TabFocus)
			if function:
				btn.clicked.connect(function)
			if not enabled:
				btn.setEnabled(False)
			if type(layout) == QGridLayout:
				layout.addWidget(btn, gridPlacement[0], gridPlacement[1], gridSpan[0], gridSpan[1])
			elif layout != None:
				layout.addWidget(btn)
			return btn

		btnLayout = QHBoxLayout()
		self.refreshBtn = mkButton(u"↻", btnLayout, self.refreshSerial, toolButton=True)
		self.serialDeviceCombo = QComboBox()
		self.serialDeviceCombo.setEditable(True)
		btnLayout.addWidget(self.serialDeviceCombo)
		self.openBtn = mkButton("Open", btnLayout, self.openPortClicked, toolButton=True)
		self.closeBtn = mkButton("Close", btnLayout, self.closePortClicked, toolButton=True)
		self.closeBtn.setDisabled(True)

		self.signals = {}
		self.signals['cd']  = QCheckBox("1/CD")
		self.signals['rx']  = QCheckBox("2/RX")
		self.signals['tx']  = QCheckBox("3/TX")
		self.signals['dtr'] = QCheckBox("4/DTR")
		self.signals['dtr'].stateChanged.connect(self.updateSerialDTR)
		self.signals['dsr'] = QCheckBox("6/DSR")
		self.signals['rts'] = QCheckBox("7/RTS")
		self.signals['rts'].stateChanged.connect(self.updateSerialRTS)
		self.signals['cts'] = QCheckBox("8/CTS")
		self.signals['ri']  = QCheckBox("9/RI")

		ledsGroupBox = QGroupBox(self)
		ledsLayout = QGridLayout(ledsGroupBox)
		signalsLayout = QHBoxLayout()
		for i, signalName in enumerate(self.signals):
			self.signals[signalName].setEnabled(False)
			signalsLayout.addWidget(self.signals[signalName])
			pin, name = self.signals[signalName].text().split('/')
			self.signals[signalName].led = LED(size=40)
			if int(pin) <= 5: x, y = (int(pin)-1)*2, 1
			else:             x, y = (int(pin)-6)*2+1, 3
			print(name, pin, x, y)
			ledsLayout.addWidget(self.signals[signalName].led, y, x, 1, 2, alignment=Qt.AlignCenter)
			ledsLayout.addWidget(QLabel(self.signals[signalName].text()), y+1, x, 1, 2, alignment=Qt.AlignCenter|Qt.AlignTop)
			self.signals[signalName].setText(name)

		l = QLabel(); l.setObjectName('top_padding')
		ledsLayout.addWidget(l, 0, 0, 1, 10, alignment=Qt.AlignCenter)
		ledsLayout.addWidget(LED(size=40, color=(127, 127, 127), enabled=True), 1, 8, 1, 2, alignment=Qt.AlignCenter)
		ledsLayout.addWidget(QLabel('5/GND'), 2, 8, 1, 2, alignment=Qt.AlignCenter|Qt.AlignTop)

		self.signals['dtr'].led.setColor((255, 0, 0))
		self.signals['rts'].led.setColor((255, 0, 0))
		self.signals['tx'].led.setColor((255, 0, 0))

		layout = QVBoxLayout(self)
		layout.addLayout(btnLayout)
		layout.addWidget(ledsGroupBox)
		layout.addLayout(signalsLayout)

		self.setWindowTitle(u"RS232 Tester")
		self.show()

		self.refreshTimer = QTimer()
		self.refreshTimer.timeout.connect(self.refresh)

	def refreshSerial(self):
		self.serialDeviceCombo.clear()
		self.serialDeviceCombo.insertItems(0, listSerialPorts())

	def openPortClicked(self):
		try:
			self.serial = serial.Serial(self.serialDeviceCombo.currentText(), timeout=0.1, write_timeout=0.1)
			self.openBtn.setDisabled(True)
			self.closeBtn.setDisabled(False)
			self.refreshBtn.setDisabled(True)
			self.serialDeviceCombo.setDisabled(True)
			self.signals['tx'].setEnabled(True)
			self.signals['dtr'].setEnabled(True)
			self.signals['rts'].setEnabled(True)
			self.refreshTimer.start(50)

		except Exception as e:
			QMessageBox.warning(self, "Fucking Error", str(e))

	def closePortClicked(self):
		self.serial.close()
		self.refreshTimer.stop()
		self.openBtn.setDisabled(False)
		self.closeBtn.setDisabled(True)
		self.refreshBtn.setDisabled(False)
		self.serialDeviceCombo.setDisabled(False)
		self.signals['tx'].setEnabled(False)
		self.signals['dtr'].setEnabled(False)
		self.signals['rts'].setEnabled(False)

		for signalName in self.signals:
			self.signals[signalName].led.enable(False)

	def updateSerialDTR(self):
		self.serial.dtr = self.signals['dtr'].isChecked()

	def updateSerialRTS(self):
		self.serial.rts = self.signals['rts'].isChecked()

	def refresh(self):
		self.signals['cd'].setChecked(self.serial.cd)
		self.signals['dtr'].setChecked(self.serial.dtr) # output signal
		self.signals['dsr'].setChecked(self.serial.dsr)
		self.signals['rts'].setChecked(self.serial.rts) # output signal
		self.signals['cts'].setChecked(self.serial.cts)
		self.signals['ri'].setChecked(self.serial.ri)

		if self.signals['tx'].isChecked():
			self.serial.write(self.msg)

		l = self.serial.in_waiting
		if l:
			rx_str = self.serial.read(l)
			self.signals['rx'].setChecked(True)
			if rx_str == self.msg:
				self.signals['rx'].led.setColor((0, 255, 0))
			else:
				self.signals['rx'].led.setColor((255, 255, 0))
				print(rx_str)
		else:
			self.signals['rx'].setChecked(False)

		for signalName in self.signals:
			self.signals[signalName].led.enable(self.signals[signalName].isChecked())


class LED(QLabel):
	def __init__(self, size=30, color=(0, 255, 0), text="", enabled=False):
		QLabel.__init__(self, text)
		self.color = color
		self.size = size
		self.enabled = enabled
		self.setFixedSize(size, size)
		self.setAlignment(Qt.AlignCenter)
		self.update()

	def enable(self, enabled=True):
		self.enabled = enabled
		self.update()

	def disable(self):
		self.enabled = False
		self.update()

	def setColor(self, color, enabled=None):
		self.color = color
		if enabled != None:
			self.enabled = enabled
		self.update()

	def update(self):
		r1, g1, b1 = self.color
		r2, g2, b2 = self.color
		if not self.enabled:
			if r1 == 0 or r1 == 0 or r1 == 0: r1, g1, b1 = r1/4, g1/6, b1/2.5; r2, g2, b2 = r2/10, g2/12, b2/6
			else: r1, g1, b1 = r1/4, g1/4, b1/4; r2, g2, b2 = r2/10, g2/10, b2/10
		else:
			r1, g1, b1 = min(255, r1+80), min(255, g1+80), min(255, b1+80)

		self.setStyleSheet("margin: 0px; padding: 0px; color: black; border-radius: %.0f; background-color: qlineargradient(spread:pad, x1:0.145, y1:0.16, x2:1, y2:1, stop:0 rgba(%d, %d, %d, 255), stop:1 rgba(%d, %d, %d, 255));" % (self.size / 2, r1, g1, b1, r2, g2, b2))


def listSerialPorts():
	result = []
	for port in serial.tools.list_ports.comports():
		result.append(tuple(port)[0])
	return result


def main():
	app = QApplication(sys.argv)
	m1 = GUI()
	ret = app.exec_()
	sys.exit(ret)

if __name__ == '__main__':
	main()
