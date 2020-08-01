# ##########################################################
# FlatCAM: 2D Post-processing for Manufacturing            #
# File Author: Marius Adrian Stanciu (c)                   #
# Date: 07/22/2020                                         #
# MIT Licence                                              #
# ##########################################################

from appEditors.AppTextEditor import AppTextEditor
from appObjects.FlatCAMCNCJob import CNCJobObject
from appGUI.GUIElements import FCTextArea, FCEntry, FCButton, FCTable
from PyQt5 import QtWidgets, QtCore, QtGui

# from io import StringIO

import logging

import gettext
import appTranslation as fcTranslate
import builtins

fcTranslate.apply_language('strings')
if '_' not in builtins.__dict__:
    _ = gettext.gettext

log = logging.getLogger('base')


class AppGCodeEditor(QtCore.QObject):

    def __init__(self, app, parent=None):
        super().__init__(parent=parent)

        self.app = app
        self.decimals = self.app.decimals
        self.plain_text = ''
        self.callback = lambda x: None

        self.ui = AppGCodeEditorUI(app=self.app)

        self.edited_obj_name = ""

        self.gcode_obj = None
        self.code_edited = ''

        # store the status of the editor so the Delete at object level will not work until the edit is finished
        self.editor_active = False
        log.debug("Initialization of the GCode Editor is finished ...")

    def set_ui(self):
        """

        :return:
        :rtype:
        """

        self.decimals = self.app.decimals

        # #############################################################################################################
        # ############# ADD a new TAB in the PLot Tab Area
        # #############################################################################################################
        self.ui.gcode_editor_tab = AppTextEditor(app=self.app, plain_text=True)

        # add the tab if it was closed
        self.app.ui.plot_tab_area.addTab(self.ui.gcode_editor_tab, '%s' % _("Code Editor"))
        self.ui.gcode_editor_tab.setObjectName('code_editor_tab')

        # delete the absolute and relative position and messages in the infobar
        self.app.ui.position_label.setText("")
        self.app.ui.rel_position_label.setText("")

        self.ui.gcode_editor_tab.code_editor.completer_enable = False
        self.ui.gcode_editor_tab.buttonRun.hide()

        # Switch plot_area to CNCJob tab
        self.app.ui.plot_tab_area.setCurrentWidget(self.ui.gcode_editor_tab)

        self.ui.gcode_editor_tab.t_frame.hide()

        self.ui.gcode_editor_tab.t_frame.show()
        self.app.proc_container.view.set_idle()
        # #############################################################################################################
        # #############################################################################################################

        self.ui.append_text.set_value(self.app.defaults["cncjob_append"])
        self.ui.prepend_text.set_value(self.app.defaults["cncjob_prepend"])

        # Remove anything else in the GUI Selected Tab
        self.app.ui.selected_scroll_area.takeWidget()
        # Put ourselves in the GUI Selected Tab
        self.app.ui.selected_scroll_area.setWidget(self.ui.edit_widget)
        # Switch notebook to Selected page
        self.app.ui.notebook.setCurrentWidget(self.app.ui.selected_tab)

        # make a new name for the new Excellon object (the one with edited content)
        self.edited_obj_name = self.gcode_obj.options['name']
        self.ui.name_entry.set_value(self.edited_obj_name)

        # #################################################################################
        # ################### SIGNALS #####################################################
        # #################################################################################
        self.ui.name_entry.returnPressed.connect(self.on_name_activate)
        self.ui.update_gcode_button.clicked.connect(self.insert_gcode)
        self.ui.exit_editor_button.clicked.connect(lambda: self.app.editor2object())

    def build_ui(self):
        """

        :return:
        :rtype:
        """

        self.ui_disconnect()

        # if the FlatCAM object is Excellon don't build the CNC Tools Table but hide it
        self.ui.cnc_tools_table.hide()
        if self.gcode_obj.cnc_tools:
            self.ui.cnc_tools_table.show()
            self.build_cnc_tools_table()

        self.ui.exc_cnc_tools_table.hide()
        if self.gcode_obj.exc_cnc_tools:
            self.ui.exc_cnc_tools_table.show()
            self.build_excellon_cnc_tools()

        self.ui_connect()

    def build_cnc_tools_table(self):
        tool_idx = 0
        row_no = 0

        n = len(self.gcode_obj.cnc_tools) + 2
        self.ui.cnc_tools_table.setRowCount(n)

        # add the Start Gcode selection
        start_item = QtWidgets.QTableWidgetItem('%s' % _("Header GCode"))
        start_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.ui.cnc_tools_table.setItem(row_no, 1, start_item)

        for dia_key, dia_value in self.gcode_obj.cnc_tools.items():

            tool_idx += 1
            row_no += 1

            t_id = QtWidgets.QTableWidgetItem('%d' % int(tool_idx))
            # id.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.ui.cnc_tools_table.setItem(row_no, 0, t_id)  # Tool name/id

            dia_item = QtWidgets.QTableWidgetItem('%.*f' % (self.decimals, float(dia_value['tooldia'])))

            offset_txt = list(str(dia_value['offset']))
            offset_txt[0] = offset_txt[0].upper()
            offset_item = QtWidgets.QTableWidgetItem(''.join(offset_txt))
            type_item = QtWidgets.QTableWidgetItem(str(dia_value['type']))
            tool_type_item = QtWidgets.QTableWidgetItem(str(dia_value['tool_type']))

            t_id.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            dia_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            offset_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            type_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            tool_type_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            self.ui.cnc_tools_table.setItem(row_no, 1, dia_item)  # Diameter
            self.ui.cnc_tools_table.setItem(row_no, 2, offset_item)  # Offset
            self.ui.cnc_tools_table.setItem(row_no, 3, type_item)  # Toolpath Type
            self.ui.cnc_tools_table.setItem(row_no, 4, tool_type_item)  # Tool Type

            tool_uid_item = QtWidgets.QTableWidgetItem(str(dia_key))
            # ## REMEMBER: THIS COLUMN IS HIDDEN IN OBJECTUI.PY # ##
            self.ui.cnc_tools_table.setItem(row_no, 5, tool_uid_item)  # Tool unique ID)

        # add the All Gcode selection
        end_item = QtWidgets.QTableWidgetItem('%s' % _("All GCode"))
        end_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.ui.cnc_tools_table.setItem(row_no + 1, 1, end_item)

        self.ui.cnc_tools_table.resizeColumnsToContents()
        self.ui.cnc_tools_table.resizeRowsToContents()

        vertical_header = self.ui.cnc_tools_table.verticalHeader()
        # vertical_header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        vertical_header.hide()
        self.ui.cnc_tools_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        horizontal_header = self.ui.cnc_tools_table.horizontalHeader()
        horizontal_header.setMinimumSectionSize(10)
        horizontal_header.setDefaultSectionSize(70)
        horizontal_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        horizontal_header.resizeSection(0, 20)
        horizontal_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(4, QtWidgets.QHeaderView.Fixed)
        horizontal_header.resizeSection(4, 40)

        # horizontal_header.setStretchLastSection(True)
        self.ui.cnc_tools_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.ui.cnc_tools_table.setColumnWidth(0, 20)
        self.ui.cnc_tools_table.setColumnWidth(4, 40)
        self.ui.cnc_tools_table.setColumnWidth(6, 17)

        # self.ui.geo_tools_table.setSortingEnabled(True)

        self.ui.cnc_tools_table.setMinimumHeight(self.ui.cnc_tools_table.getHeight())
        self.ui.cnc_tools_table.setMaximumHeight(self.ui.cnc_tools_table.getHeight())

    def build_excellon_cnc_tools(self):
        """

        :return:
        :rtype:
        """

        tool_idx = 0
        row_no = 0

        n = len(self.gcode_obj.exc_cnc_tools) + 2
        self.ui.exc_cnc_tools_table.setRowCount(n)

        # add the Start Gcode selection
        start_item = QtWidgets.QTableWidgetItem('%s' % _("Header GCode"))
        start_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.ui.exc_cnc_tools_table.setItem(row_no, 1, start_item)

        for tooldia_key, dia_value in  self.gcode_obj.exc_cnc_tools.items():

            tool_idx += 1
            row_no += 1

            t_id = QtWidgets.QTableWidgetItem('%d' % int(tool_idx))
            dia_item = QtWidgets.QTableWidgetItem('%.*f' % (self.decimals, float(tooldia_key)))
            nr_drills_item = QtWidgets.QTableWidgetItem('%d' % int(dia_value['nr_drills']))
            nr_slots_item = QtWidgets.QTableWidgetItem('%d' % int(dia_value['nr_slots']))
            cutz_item = QtWidgets.QTableWidgetItem('%.*f' % (
                self.decimals, float(dia_value['offset']) +  float(dia_value['data']['tools_drill_cutz'])))

            t_id.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            dia_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            nr_drills_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            nr_slots_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            cutz_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            self.ui.exc_cnc_tools_table.setItem(row_no, 0, t_id)  # Tool name/id
            self.ui.exc_cnc_tools_table.setItem(row_no, 1, dia_item)  # Diameter
            self.ui.exc_cnc_tools_table.setItem(row_no, 2, nr_drills_item)  # Nr of drills
            self.ui.exc_cnc_tools_table.setItem(row_no, 3, nr_slots_item)  # Nr of slots

            tool_uid_item = QtWidgets.QTableWidgetItem(str(dia_value['tool']))
            # ## REMEMBER: THIS COLUMN IS HIDDEN IN OBJECTUI.PY # ##
            self.ui.exc_cnc_tools_table.setItem(row_no, 4, tool_uid_item)  # Tool unique ID)
            self.ui.exc_cnc_tools_table.setItem(row_no, 5, cutz_item)

        # add the All Gcode selection
        end_item = QtWidgets.QTableWidgetItem('%s' % _("All GCode"))
        end_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.ui.exc_cnc_tools_table.setItem(row_no + 1, 1, end_item)

        self.ui.exc_cnc_tools_table.resizeColumnsToContents()
        self.ui.exc_cnc_tools_table.resizeRowsToContents()

        vertical_header = self.ui.exc_cnc_tools_table.verticalHeader()
        vertical_header.hide()
        self.ui.exc_cnc_tools_table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        horizontal_header = self.ui.exc_cnc_tools_table.horizontalHeader()
        horizontal_header.setMinimumSectionSize(10)
        horizontal_header.setDefaultSectionSize(70)
        horizontal_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        horizontal_header.resizeSection(0, 20)
        horizontal_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        horizontal_header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)

        # horizontal_header.setStretchLastSection(True)
        self.ui.exc_cnc_tools_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.ui.exc_cnc_tools_table.setColumnWidth(0, 20)
        self.ui.exc_cnc_tools_table.setColumnWidth(6, 17)

        self.ui.exc_cnc_tools_table.setMinimumHeight(self.ui.exc_cnc_tools_table.getHeight())
        self.ui.exc_cnc_tools_table.setMaximumHeight(self.ui.exc_cnc_tools_table.getHeight())

    def ui_connect(self):
        """

        :return:
        :rtype:
        """
        # rows selected
        if self.gcode_obj.cnc_tools:
            self.ui.cnc_tools_table.clicked.connect(self.on_row_selection_change)
            self.ui.cnc_tools_table.horizontalHeader().sectionClicked.connect(self.on_toggle_all_rows)
        if self.gcode_obj.exc_cnc_tools:
            self.ui.exc_cnc_tools_table.clicked.connect(self.on_row_selection_change)
            self.ui.exc_cnc_tools_table.horizontalHeader().sectionClicked.connect(self.on_toggle_all_rows)

    def ui_disconnect(self):
        """

        :return:
        :rtype:
        """
        # rows selected
        if self.gcode_obj.cnc_tools:
            try:
                self.ui.cnc_tools_table.clicked.disconnect(self.on_row_selection_change)
            except (TypeError, AttributeError):
                pass
            try:
                self.ui.cnc_tools_table.horizontalHeader().sectionClicked.disconnect(self.on_toggle_all_rows)
            except (TypeError, AttributeError):
                pass

        if self.gcode_obj.exc_cnc_tools:
            try:
                self.ui.exc_cnc_tools_table.clicked.disconnect(self.on_row_selection_change)
            except (TypeError, AttributeError):
                pass
            try:
                self.ui.exc_cnc_tools_table.horizontalHeader().sectionClicked.disconnect(self.on_toggle_all_rows)
            except (TypeError, AttributeError):
                pass

    def on_row_selection_change(self):
        """

        :return:
        :rtype:
        """
        if self.gcode_obj.cnc_tools:
            sel_model = self.ui.cnc_tools_table.selectionModel()
        elif self.gcode_obj.exc_cnc_tools:
            sel_model = self.ui.exc_cnc_tools_table.selectionModel()
        else:
            return
        sel_indexes = sel_model.selectedIndexes()

        # it will iterate over all indexes which means all items in all columns too but I'm interested only on rows
        sel_rows = set()
        for idx in sel_indexes:
            sel_rows.add(idx.row())

    def on_toggle_all_rows(self):
        """

        :return:
        :rtype:
        """
        if self.gcode_obj.cnc_tools:
            sel_model = self.ui.cnc_tools_table.selectionModel()
        elif self.gcode_obj.exc_cnc_tools:
            sel_model = self.ui.exc_cnc_tools_table.selectionModel()
        else:
            return
        sel_indexes = sel_model.selectedIndexes()

        # it will iterate over all indexes which means all items in all columns too but I'm interested only on rows
        sel_rows = set()
        for idx in sel_indexes:
            sel_rows.add(idx.row())

        if self.gcode_obj.cnc_tools:
            if len(sel_rows) == self.ui.cnc_tools_table.rowCount():
                self.ui.cnc_tools_table.clearSelection()
            else:
                self.ui.cnc_tools_table.selectAll()
        elif self.gcode_obj.exc_cnc_tools:
            if len(sel_rows) == self.ui.exc_cnc_tools_table.rowCount():
                self.ui.exc_cnc_tools_table.clearSelection()
            else:
                self.ui.exc_cnc_tools_table.selectAll()
        else:
            return

    def handleTextChanged(self):
        """

        :return:
        :rtype:
        """
        # enable = not self.ui.code_editor.document().isEmpty()
        # self.ui.buttonPrint.setEnabled(enable)
        # self.ui.buttonPreview.setEnabled(enable)

        self.buttonSave.setStyleSheet("QPushButton {color: red;}")
        self.buttonSave.setIcon(QtGui.QIcon(self.app.resource_location + '/save_as_red.png'))

    def insert_gcode(self):
        """

        :return:
        :rtype:
        """
        pass

    def edit_fcgcode(self, cnc_obj):
        """

        :param cnc_obj:
        :type cnc_obj:
        :return:
        :rtype:
        """
        assert isinstance(cnc_obj, CNCJobObject)
        self.gcode_obj = cnc_obj

        gcode_text = self.gcode_obj.source_file

        self.set_ui()
        self.build_ui()

        # then append the text from GCode to the text editor
        self.ui.gcode_editor_tab.load_text(gcode_text, move_to_start=True, clear_text=True)
        self.app.inform.emit('[success] %s...' % _('Loaded Machine Code into Code Editor'))

    def update_fcgcode(self, edited_obj):
        """

        :return:
        :rtype:
        """
        preamble = str(self.ui.prepend_text.get_value())
        postamble = str(self.ui.append_text.get_value())
        my_gcode = self.ui.gcode_editor_tab.code_editor.toPlainText()
        self.gcode_obj.source_file = my_gcode

        self.ui.gcode_editor_tab.buttonSave.setStyleSheet("")
        self.ui.gcode_editor_tab.buttonSave.setIcon(QtGui.QIcon(self.app.resource_location + '/save_as.png'))

    def on_open_gcode(self):
        """

        :return:
        :rtype:
        """
        _filter_ = "G-Code Files (*.nc);; G-Code Files (*.txt);; G-Code Files (*.tap);; G-Code Files (*.cnc);; " \
                   "All Files (*.*)"

        path, _f = QtWidgets.QFileDialog.getOpenFileName(
            caption=_('Open file'), directory=self.app.get_last_folder(), filter=_filter_)

        if path:
            file = QtCore.QFile(path)
            if file.open(QtCore.QIODevice.ReadOnly):
                stream = QtCore.QTextStream(file)
                self.code_edited = stream.readAll()
                self.ui.gcode_editor_tab.load_text(self.code_edited, move_to_start=True, clear_text=True)
                file.close()

    def on_name_activate(self):
        self.edited_obj_name = self.ui.name_entry.get_value()

class AppGCodeEditorUI:
    def __init__(self, app):
        self.app = app

        # Number of decimals used by tools in this class
        self.decimals = self.app.decimals

        # ## Current application units in Upper Case
        self.units = self.app.defaults['units'].upper()

        # self.setSizePolicy(
        #     QtWidgets.QSizePolicy.MinimumExpanding,
        #     QtWidgets.QSizePolicy.MinimumExpanding
        # )

        self.gcode_editor_tab = None

        self.edit_widget = QtWidgets.QWidget()
        # ## Box for custom widgets
        # This gets populated in offspring implementations.
        layout = QtWidgets.QVBoxLayout()
        self.edit_widget.setLayout(layout)

        # add a frame and inside add a vertical box layout. Inside this vbox layout I add all the Drills widgets
        # this way I can hide/show the frame
        self.edit_frame = QtWidgets.QFrame()
        self.edit_frame.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.edit_frame)
        self.edit_box = QtWidgets.QVBoxLayout()
        self.edit_box.setContentsMargins(0, 0, 0, 0)
        self.edit_frame.setLayout(self.edit_box)

        # ## Page Title box (spacing between children)
        self.title_box = QtWidgets.QHBoxLayout()
        self.edit_box.addLayout(self.title_box)

        # ## Page Title icon
        pixmap = QtGui.QPixmap(self.app.resource_location + '/flatcam_icon32.png')
        self.icon = QtWidgets.QLabel()
        self.icon.setPixmap(pixmap)
        self.title_box.addWidget(self.icon, stretch=0)

        # ## Title label
        self.title_label = QtWidgets.QLabel("<font size=5><b>%s</b></font>" % _('GCode Editor'))
        self.title_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.title_box.addWidget(self.title_label, stretch=1)

        # ## Object name
        self.name_box = QtWidgets.QHBoxLayout()
        self.edit_box.addLayout(self.name_box)
        name_label = QtWidgets.QLabel(_("Name:"))
        self.name_box.addWidget(name_label)
        self.name_entry = FCEntry()
        self.name_box.addWidget(self.name_entry)

        separator_line = QtWidgets.QFrame()
        separator_line.setFrameShape(QtWidgets.QFrame.HLine)
        separator_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.edit_box.addWidget(separator_line)

        # CNC Tools Table when made out of Geometry
        self.cnc_tools_table = FCTable()
        self.cnc_tools_table.setSortingEnabled(False)
        self.cnc_tools_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.edit_box.addWidget(self.cnc_tools_table)

        self.cnc_tools_table.setColumnCount(6)
        self.cnc_tools_table.setColumnWidth(0, 20)
        self.cnc_tools_table.setHorizontalHeaderLabels(['#', _('Dia'), _('Offset'), _('Type'), _('TT'), ''])
        self.cnc_tools_table.setColumnHidden(5, True)

        # CNC Tools Table when made out of Excellon
        self.exc_cnc_tools_table = FCTable()
        self.exc_cnc_tools_table.setSortingEnabled(False)
        self.exc_cnc_tools_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.edit_box.addWidget(self.exc_cnc_tools_table)

        self.exc_cnc_tools_table.setColumnCount(6)
        self.exc_cnc_tools_table.setColumnWidth(0, 20)
        self.exc_cnc_tools_table.setHorizontalHeaderLabels(['#', _('Dia'), _('Drills'), _('Slots'), '', _("Cut Z")])
        self.exc_cnc_tools_table.setColumnHidden(4, True)

        separator_line = QtWidgets.QFrame()
        separator_line.setFrameShape(QtWidgets.QFrame.HLine)
        separator_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.edit_box.addWidget(separator_line)

        # Prepend text to GCode
        prependlabel = QtWidgets.QLabel('%s:' % _('Prepend to CNC Code'))
        prependlabel.setToolTip(
            _("Type here any G-Code commands you would\n"
              "like to add at the beginning of the G-Code file.")
        )
        self.edit_box.addWidget(prependlabel)

        self.prepend_text = FCTextArea()
        self.prepend_text.setPlaceholderText(
            _("Type here any G-Code commands you would\n"
              "like to add at the beginning of the G-Code file.")
        )
        self.edit_box.addWidget(self.prepend_text)

        # Append text to GCode
        appendlabel = QtWidgets.QLabel('%s:' % _('Append to CNC Code'))
        appendlabel.setToolTip(
            _("Type here any G-Code commands you would\n"
              "like to append to the generated file.\n"
              "I.e.: M2 (End of program)")
        )
        self.edit_box.addWidget(appendlabel)

        self.append_text = FCTextArea()
        self.append_text.setPlaceholderText(
            _("Type here any G-Code commands you would\n"
              "like to append to the generated file.\n"
              "I.e.: M2 (End of program)")
        )
        self.edit_box.addWidget(self.append_text)

        h_lay = QtWidgets.QHBoxLayout()
        h_lay.setAlignment(QtCore.Qt.AlignVCenter)
        self.edit_box.addLayout(h_lay)

        # GO Button
        self.update_gcode_button = FCButton(_('Update Code'))
        # self.update_gcode_button.setIcon(QtGui.QIcon(self.app.resource_location + '/save_as.png'))
        self.update_gcode_button.setToolTip(
            _("Update the Gcode in the Editor with the values\n"
              "in the 'Prepend' and 'Append' text boxes.")
        )

        h_lay.addWidget(self.update_gcode_button)

        layout.addStretch()

        # Editor
        self.exit_editor_button = FCButton(_('Exit Editor'))
        self.exit_editor_button.setIcon(QtGui.QIcon(self.app.resource_location + '/power16.png'))
        self.exit_editor_button.setToolTip(
            _("Exit from Editor.")
        )
        self.exit_editor_button.setStyleSheet("""
                                          QPushButton
                                          {
                                              font-weight: bold;
                                          }
                                          """)
        layout.addWidget(self.exit_editor_button)
        # ############################ FINSIHED GUI ##################################################################
        # #############################################################################################################

    def confirmation_message(self, accepted, minval, maxval):
        if accepted is False:
            self.app.inform[str, bool].emit('[WARNING_NOTCL] %s: [%.*f, %.*f]' % (_("Edited value is out of range"),
                                                                                  self.decimals,
                                                                                  minval,
                                                                                  self.decimals,
                                                                                  maxval), False)
        else:
            self.app.inform[str, bool].emit('[success] %s' % _("Edited value is within limits."), False)

    def confirmation_message_int(self, accepted, minval, maxval):
        if accepted is False:
            self.app.inform[str, bool].emit('[WARNING_NOTCL] %s: [%d, %d]' %
                                            (_("Edited value is out of range"), minval, maxval), False)
        else:
            self.app.inform[str, bool].emit('[success] %s' % _("Edited value is within limits."), False)
