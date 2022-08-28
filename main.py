import sys
import os
import re
import tempfile
from string import Template
import shutil
from time import sleep

from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import *
from qt.QFileEdit import QFileEdit
from qt.MainForm import Ui_mainWindow

from config import presets
from config import values as v


def generate_ffmpeg_cmdline(file_in, ass_in, output_path, vcodec, acodec, vencoding, rc, rcparam1, rcparam2):
    s_dict = dict()
    s_dict["file_in"] = file_in
    s_dict["out_file"] = output_path

    if ass_in is None:
        ffmpeg_first_str = "ffmpeg $hwaccel_opt -i $file_in -c:v $vcodec $vcodec_opt -c:a $acodec" \
                           " $acodec_opt $out_file "
    else:
        ffmpeg_first_str = "ffmpeg $hwaccel_opt -i $file_in -vf \"ass=$ass_in\" -c:v $vcodec $vcodec_opt -c:a $acodec" \
                           " $acodec_opt $out_file "
        s_dict["ass_in"] = ass_in
    ffmpeg_first = Template(ffmpeg_first_str)

    # Determine parameters for video encoding.
    if vcodec == v.vcodec["soft"]:
        s_dict["hwaccel_opt"] = ""
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "libx264"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "libx265"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-crf " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = ("-b:v " + rcparam1 + " "
                                    + "-minrate " + rcparam1 + " "
                                    + "-maxrate " + rcparam1)
        elif rc == v.rc["vbr2"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -pass 2 -maxrate:v" + rcparam2
        elif rc == v.rc["vbr"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v" + rcparam2
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = "-preset slow -b:v " + rcparam1 + " -maxrate:v" + rcparam2

    elif vcodec == v.vcodec["nvenc"]:
        s_dict["hwaccel_opt"] = "-hwaccel cuda"
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "h264_nvenc"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "hevc_nvenc"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-rc constqp -qp " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = "-rc cbr_hq -cbr true -b:v " + rcparam1
        elif rc == v.rc["vbr2"]:
            s_dict["vcodec_opt"] = ("-rc vbr -2pass true " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
        elif rc == v.rc["vbr"]:
            s_dict["vcodec_opt"] = ("-rc vbr " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = ("-rc vbr_hq " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
    elif vcodec == v.vcodec["iqsv"]:
        s_dict["hwaccel_opt"] = "-hwaccel qsv -init_hw_device qsv hw -filter_hw_device hw"
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "h264_qsv"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "hevc_qsv"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-global_quality " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v " + rcparam1
        elif rc == v.rc["vbr"] or rc == v.rc["vbr2"]:  # Intel QSV does not support 2-pass
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v " + rcparam2
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = "-preset slow -b:v " + rcparam1 + " -maxrate:v " + rcparam2

    s_dict["acodec"] = "aac"
    s_dict["acodec_opt"] = "-b:a 320k"

    return ffmpeg_first.substitute(s_dict)


def gen_ffmpeg_cmdline_optonly(vcodec, acodec, vencoding, rc, rcparam1, rcparam2):
    s_dict = dict()
    ffmpeg_first_str = "-c:v $vcodec $vcodec_opt -c:a $acodec $acodec_opt"
    ffmpeg_first = Template(ffmpeg_first_str)

    # Determine parameters for video encoding.
    if vcodec == v.vcodec["soft"]:
        s_dict["hwaccel_opt"] = ""
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "libx264"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "libx265"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-crf " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = ("-b:v " + rcparam1 + " "
                                    + "-minrate " + rcparam1 + " "
                                    + "-maxrate " + rcparam1)
        elif rc == v.rc["vbr2"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -pass 2 -maxrate:v" + rcparam2
        elif rc == v.rc["vbr"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v" + rcparam2
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = "-preset slow -b:v " + rcparam1 + " -maxrate:v" + rcparam2

    elif vcodec == v.vcodec["nvenc"]:
        s_dict["hwaccel_opt"] = "-hwaccel cuda"
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "h264_nvenc"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "hevc_nvenc"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-rc constqp -qp " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = "-rc cbr_hq -cbr true -b:v " + rcparam1
        elif rc == v.rc["vbr2"]:
            s_dict["vcodec_opt"] = ("-rc vbr -2pass true " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
        elif rc == v.rc["vbr"]:
            s_dict["vcodec_opt"] = ("-rc vbr " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = ("-rc vbr_hq " +
                                    "-b:v " + rcparam1 + " " +
                                    "-maxrate:v " + rcparam2)
    elif vcodec == v.vcodec["iqsv"]:
        s_dict["hwaccel_opt"] = "-hwaccel qsv -init_hw_device qsv hw -filter_hw_device hw"
        if vencoding == v.vencoding['h264']:
            s_dict["vcodec"] = "h264_qsv"
        elif vencoding == v.vencoding['h265']:
            s_dict["vcodec"] = "hevc_qsv"

        if rc == v.rc["cqp"]:
            s_dict["vcodec_opt"] = "-global_quality " + rcparam1
        elif rc == v.rc["cbr"]:
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v " + rcparam1
        elif rc == v.rc["vbr"] or rc == v.rc["vbr2"]:  # Intel QSV does not support 2-pass
            s_dict["vcodec_opt"] = "-b:v " + rcparam1 + " -maxrate:v " + rcparam2
        elif rc == v.rc["vbrhq"]:
            s_dict["vcodec_opt"] = "-preset slow -b:v " + rcparam1 + " -maxrate:v " + rcparam2

    s_dict["acodec"] = "aac"
    s_dict["acodec_opt"] = "-b:a 320k"

    return ffmpeg_first.substitute(s_dict)


def exec_new_window(command):
    if sys.platform.startswith("win"):
        os.system('start cmd /k "' + command + '"')
    elif sys.platform.startswith("darwin"):
        from applescript import tell
        tell.app('Terminal', 'do script "' + command + '"')


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_mainWindow()
        self.ui.setupUi(self)

        self.btn_video_browse = self.findChild(QPushButton, 'btnBrowseVideo')
        self.line_video_path = self.findChild(QFileEdit, 'lineEditVideo')
        self.line_ass_path = self.findChild(QFileEdit, 'lineEditSubtitle')
        self.line_output_path = self.findChild(QFileEdit, 'lineEditOutput')
        self.btn_ass_browse = self.findChild(QPushButton, 'btnBrowseAss')
        self.btn_set_output = self.findChild(QPushButton, 'btnSetOutput')
        self.btn_apply_preset = self.findChild(QPushButton, 'btnApplyPreset')
        self.btn_start = self.findChild(QPushButton, 'btnStart')

        self.check_rmv_ad = self.findChild(QCheckBox, 'chkRemoveAd')
        self.entry_start_frame = self.findChild(QLineEdit, 'lineStartFrame')
        self.entry_end_frame = self.findChild(QLineEdit, 'lineEndFrame')

        self.select_preset = self.findChild(QComboBox, 'selectPreset')
        self.select_vencoding = self.findChild(QComboBox, 'selectEncoding')
        self.select_vcodec = self.findChild(QComboBox, 'selectVCodec')
        self.select_aencoding = self.findChild(QComboBox, 'selectACodec')
        self.select_packaging = self.findChild(QComboBox, 'selectPackaging')
        self.select_rate_control = self.findChild(QComboBox, 'selectRateControl')
        self.label_rc_param1 = self.findChild(QLabel, 'rcParam1')
        self.label_rc_param2 = self.findChild(QLabel, 'rcParam2')
        self.label_rc_entry1 = self.findChild(QLineEdit, 'rcEntry1')
        self.label_rc_entry2 = self.findChild(QLineEdit, 'rcEntry2')

        self.update_selectors()

        self.select_rate_control.currentIndexChanged.connect(self.event_rc_changed)
        self.select_packaging.currentIndexChanged.connect(self.update_extension)
        self.btn_video_browse.clicked.connect(self.browse_video)
        self.btn_ass_browse.clicked.connect(self.browse_ass)
        self.btn_apply_preset.clicked.connect(self.event_apply_preset)
        self.btn_start.clicked.connect(self.execute)

    def update_extension(self):
        ext = self.select_packaging.currentText()
        for key, val in v.format.items():
            if val == ext:
                out_filename = self.line_output_path.text()
                if out_filename.endswith("\""):
                    out_filename = re.sub("\\.[^.]+\"$", "." + key + "\"", out_filename)
                else:
                    out_filename = re.sub("\\.[^.]+$", "." + key, out_filename)
                self.line_output_path.setText(out_filename)

    def update_selectors(self):
        self.select_preset.clear()
        self.select_preset.addItems(presets.presets_dict.keys())

        self.select_vencoding.clear()
        self.select_vencoding.addItems(v.vencoding.values())

        self.select_vcodec.clear()
        self.select_vcodec.addItems(v.vcodec.values())

        self.select_aencoding.clear()
        self.select_aencoding.addItems(v.acodec.values())

        self.select_packaging.clear()
        self.select_packaging.addItems(v.format.values())

        self.select_rate_control.clear()
        self.select_rate_control.addItems(v.rc.values())

    def browse_video(self):
        _fopen = QFileDialog()
        _fopen.AcceptMode = QFileDialog.AcceptOpen
        _fopen.FileMode = QFileDialog.ExistingFile

        filename, _filter = _fopen.getOpenFileName()
        self.line_video_path.setText(filename)

    def browse_ass(self):
        _fopen = QFileDialog()
        _fopen.AcceptMode = QFileDialog.AcceptOpen
        _fopen.FileMode = QFileDialog.ExistingFile

        filename, _filter = _fopen.getOpenFileName()
        self.line_ass_path.setText(filename)

    def browse_save(self):
        _fsave = QFileDialog()
        _fsave.AcceptMode = QFileDialog.AcceptSave
        _fsave.FileMode = QFileDialog.AnyFile

        filename, _filter = _fsave.getOpenFileName()
        self.line_output_path.setText(filename)

    def event_rc_changed(self):
        curr_item = self.select_rate_control.currentText()
        if (curr_item == "VBR") or (curr_item == "VBR_HQ") or (curr_item == "VBR 2-pass"):
            self.label_rc_param1.setText("目标比特率")
            self.label_rc_param2.setText("最大比特率")
            self.label_rc_entry2.setEnabled(True)
            self.label_rc_param2.setEnabled(True)
        elif curr_item == "Constant QP":
            self.label_rc_param1.setText("质量指数")
            self.label_rc_param2.setText("不适用")
            self.label_rc_entry2.setEnabled(False)
            self.label_rc_param2.setEnabled(False)
        elif curr_item == "CBR":
            self.label_rc_param1.setText("比特率")
            self.label_rc_param2.setText("不适用")
            self.label_rc_entry2.setEnabled(False)
            self.label_rc_param2.setEnabled(False)

    def event_apply_preset(self):
        curr_item = self.select_preset.currentText()
        if curr_item in presets.presets_dict:
            config = presets.presets_dict.get(curr_item)
            if "encoding" in config:
                self.select_vencoding.setCurrentIndex(
                    self.select_vencoding.findText(config["encoding"]))
            if "vcodec" in config:
                self.select_vcodec.setCurrentIndex(
                    self.select_vcodec.findText(config["vcodec"]))
            if "acodec" in config:
                self.select_aencoding.setCurrentIndex(
                    self.select_aencoding.findText(config["acodec"]))
            if "format" in config:
                self.select_packaging.setCurrentIndex(
                    self.select_packaging.findText(config["format"]))
            if "rc" in config:
                self.select_rate_control.setCurrentIndex(
                    self.select_rate_control.findText(config["rc"]))
                self.event_rc_changed()
            if "param1" in config:
                self.label_rc_entry1.setText(config["param1"])
            if "param2" in config:
                self.label_rc_entry2.setText(config["param2"])

    def execute(self):
        file_in = self.line_video_path.text().strip()
        if not (file_in.startswith("\"") and file_in.endswith("\"")):
            file_in = "\"" + file_in + "\""

        ass_in = self.line_ass_path.text().strip()
        
        if ass_in.startswith("\"") and ass_in.endswith("\""):
            ass_in = ass_in.lstrip("\"").rstrip("\"")

        # ass_in = ass_in\
        #     .replace("\\", r"\\\\")\
        #     .replace(r",", r"\\\,")\
        #     .replace(r"'", r"\\\'")\
        #     .replace(":", r"\\\:")\
        #     .replace("[", r"\\\[")\
        #     .replace("]", r"\\\]")

        output_path = self.line_output_path.text().strip()
        if not (output_path.startswith("\"") and output_path.endswith("\"")):
            output_path = "\"" + output_path + "\""

        vcodec = self.select_vcodec.currentText()
        acodec = self.select_aencoding.currentText()
        vencoding = self.select_vencoding.currentText()
        rc = self.select_rate_control.currentText()
        rcparam1 = self.label_rc_entry1.text()
        rcparam2 = self.label_rc_entry2.text()

        if self.check_rmv_ad.isChecked():
            # Step 1. Create the file.
            temp_dir = os.path.join(tempfile.gettempdir(), "video-packer")

            # 遇到一个很神奇的bug，直接os.makedirs()会失败
            # 它会一路往上找到根盘符，然后说无法创建目录"C:"
            try:
                os.makedirs(temp_dir, exist_ok=True)
            except:
                os.system("mkdir \"" + temp_dir + "\"")

            ass_file_copy = os.path.join(temp_dir, 'sub.ass')
            temp_filename = os.path.join(temp_dir, "temp.mp4")
            part1_filename = os.path.join(temp_dir, "part1.mp4")
            part2_filename = os.path.join(temp_dir, "part2.mp4")
            ffconcat_filename = os.path.join(temp_dir, "comb.ffconcat")
            bash_file = os.path.join(temp_dir, "start.bat")

            try:
                os.remove(temp_filename)
            except FileNotFoundError:
                pass
            
            with open(ass_in, 'rb') as f1, open(ass_file_copy, 'wb') as f2:
                shutil.copyfileobj(f1, f2)
                
            with open(ffconcat_filename, 'w') as cfile:
                cfile.writelines(['file part1.mp4' + os.linesep, 'file part2.mp4' + os.linesep])

            ad_begin = self.entry_start_frame.text()
            ad_end = self.entry_end_frame.text()
            with open(bash_file, 'w') as bfile:
                bfile.writelines([
                    "@echo off" + os.linesep,
                    "cd /d " + temp_dir + os.linesep,
                    generate_ffmpeg_cmdline(file_in, 'sub.ass', temp_filename, vcodec, acodec, vencoding, rc, rcparam1,
                                            rcparam2) + os.linesep,
                    "ffmpeg -y -i temp.mp4 -t " + ad_begin + " " + gen_ffmpeg_cmdline_optonly(vcodec, acodec, vencoding, rc, rcparam1, rcparam2) + " part1.mp4" + os.linesep,
                    "ffmpeg -y -ss " + ad_end + " -i temp.mp4 " + gen_ffmpeg_cmdline_optonly(vcodec, acodec, vencoding, rc, rcparam1, rcparam2) + " part2.mp4" + os.linesep,
                    "ffmpeg -y -safe 0 -f concat -i comb.ffconcat -c copy " + output_path + os.linesep,
                    "del part1.mp4" + os.linesep,
                    "del part2.mp4" + os.linesep,
                    "del temp.mp4" + os.linesep,
                    "del comb.ffconcat" + os.linesep,
                    # "del start.bat" + os.linesep
                ])

            exec_new_window('"' + bash_file + '"')

        else:
            final_command = generate_ffmpeg_cmdline(file_in, ass_in, output_path, vcodec, acodec, vencoding, rc,
                                                    rcparam1, rcparam2)
            print(final_command)
            exec_new_window(final_command)


if __name__ == "__main__":
    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
