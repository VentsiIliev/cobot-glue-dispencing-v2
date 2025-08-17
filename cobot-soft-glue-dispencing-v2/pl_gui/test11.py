import sys
from PyQt5 import QtWidgets

# create app
app = QtWidgets.QApplication(sys.argv)

# create list widget
list_widget = QtWidgets.QListWidget()

# populate list widget with dummy items
for index in range(100):
    list_widget.addItem(QtWidgets.QListWidgetItem('item {}'.format(index)))

# THIS IS THE IMPORTANT PART: set the scroll mode
list_widget.setVerticalScrollMode(list_widget.ScrollPerPixel)

# OPTIONAL: enable pan by mouse (and one-finger pan)
QtWidgets.QScroller.grabGesture(list_widget.viewport(),
                                QtWidgets.QScroller.LeftMouseButtonGesture)

# show the list widget
list_widget.show()

# run the event loop
app.exec_()