from PySide6.QtWidgets import QApplication, QMainWindow, QLineEdit, QTreeWidgetItem, QListWidgetItem, QFileDialog, QTableWidgetItem, QAbstractScrollArea, QComboBox, QAbstractItemView, QItemDelegate, QStyledItemDelegate, QLabel, QMessageBox
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool, Qt, QSortFilterProxyModel
from PySide6.QtGui import QScreen
from main_window import Ui_MainWindow
from textout import clearScreen, print_logo
from web_fetch import WEBManipulator
import os
import sys
import configparser
import cryptocode
import traceback
import pickle
import re
import pandas as pd
import xlrd
import winsound as sd
import openpyxl
from collections import OrderedDict
from webdriver_manager.chrome import ChromeDriverManager
import xlwings as xw

PROGRAM_TITLE = '연관검색어 추출'
VERSION = '0.0.10'
# xlwings로 파일 저장
# 이어서 받기 기능 추가

MADE_BY = "LEW"
ENCRYPT_KEY = "fhfkekjrh2@hdjs"

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)
    ret = Signal(int)
    retMsg = Signal(str)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        print(self.kwargs)

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress
        self.kwargs['ret_callback'] = self.signals.ret
        self.kwargs['regMsg_callback'] = self.signals.retMsg

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

def beepsound():
    sd.PlaySound("SystemExit", sd.SND_ALIAS)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle(f'{PROGRAM_TITLE} {VERSION} ■■■■ 만든이 {MADE_BY}')

        self.pushButton_5.clicked.connect(self.get_naver_keyword)
        self.pushButton_7.clicked.connect(self.get_coupang_keyword)
        self.pushButton_8.clicked.connect(self.get_all_site_thread_run)
        self.pushButton.clicked.connect(self.select_excel)
        self.pushButton_2.clicked.connect(self.open_excel)
        self.pushButton_3.clicked.connect(self.select_out_path)
        self.pushButton_4.clicked.connect(self.open_out_path)
        self.pushButton_6.clicked.connect(self.select_filter_excel)
        self.pushButton_9.clicked.connect(self.open_filter_excel)

        self.pause = {'state':False}
        self.save_my_category_enabled = True

        self.threadpool = QThreadPool()

        self.category = {}
        self.df_keyword = pd.DataFrame()
        self.keywords = []

        # load config
        config = configparser.ConfigParser()
        config.read('config.ini', encoding='UTF-8')
        try:
            self.lineEdit_7.setText(config['DEFAULT']['loading_wait_time'])
            self.lineEdit_9.setText(config['DEFAULT']['excel_file'])
            self.lineEdit.setText(config['DEFAULT']['out_excel_file'])
            self.lineEdit_2.setText(config['DEFAULT']['filter_excel_file'])
            if config['DEFAULT']['resume_download'] == '1':
                self.checkBox.setChecked(True)
            else:
                self.checkBox.setChecked(False)
            # rect = self.geometry()
            # self.setGeometry(rect.left, rect.top, int(config['DEFAULT']['width']), int(config['DEFAULT']['height']))
            self.resize(int(config['DEFAULT']['width']), int(config['DEFAULT']['height']))
        except Exception as e:
            print('exception when loading config')
            print(e)
            self.lineEdit_7.setText('4-6')

        driver_path = ChromeDriverManager().install()
        print(driver_path)
        print(os.path.dirname(driver_path).split("\\"))
        self.label_13.setText(os.path.dirname(driver_path).split("\\")[-2])

    def load_excel(self):
        filename = self.lineEdit_9.text()
        try:
            self.df_keyword = pd.read_excel(filename)
            self.df_keyword = self.df_keyword.fillna('')
            print(self.df_keyword)
            print(self.df_keyword['입력키워드'].tolist())
            self.keywords = self.df_keyword['입력키워드'].tolist()

            filename_filter = self.lineEdit_2.text()
            xl = pd.ExcelFile(filename_filter)
            print(f'제외 엑셀파일 시트목록:{xl.sheet_names}')
            if '제외' not in xl.sheet_names:
                print('입력 엑셀파일에 제외 시트가 없습니다')
                return
    
            self.filters = pd.read_excel(filename_filter, '제외')
            if '연관키워드 제외목록' not in self.filters.columns.tolist():
                print('제외 시트에 "연관키워드 제외목록" 열이 없습니다')
            if '마누태그 키워드 제외목록' not in self.filters.columns.tolist():
                print('제외 시트에 "마누태그 키워드 제외목록" 열이 없습니다')

        except FileNotFoundError:
            print('이지위너 엑셀 파일 설정안됨. 이지위너 엑셀 파일을 설정해주시기 바랍니다.')

    def select_excel(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Open File")
        dialog.setNameFilter("xlsx files (*.xlsx);;All Files (*)")
        if dialog.exec():
            filename = dialog.selectedFiles()[0]
            self.lineEdit_9.setText(filename)
            print("Selected file:", filename)

    def open_excel(self):
        os.system('start excel.exe "%s"' % (self.lineEdit_9.text(), ))

    def select_filter_excel(self):
        dialog = QFileDialog(self)
        dialog.setWindowTitle("Open File")
        dialog.setNameFilter("xlsx files (*.xlsx);;All Files (*)")
        if dialog.exec():
            filename = dialog.selectedFiles()[0]
            self.lineEdit_2.setText(filename)
            print("Selected file:", filename)

    def open_filter_excel(self):
        os.system('start excel.exe "%s"' % (self.lineEdit_2.text(), ))

    def select_out_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.lineEdit.setText(folder)

    def open_out_path(self):
        path = self.lineEdit.text()
        path = os.path.realpath(path)
        os.startfile(path)

    def pause_handler(self):
        print('pause_handler')
        self.pause['state'] = True

    def program_exit(self):
        config = configparser.ConfigParser()
        config['DEFAULT']['width'] = str(self.width())
        config['DEFAULT']['height'] = str(self.height())
        config['DEFAULT']['loading_wait_time'] = self.lineEdit_7.text()
        config['DEFAULT']['excel_file'] = self.lineEdit_9.text()
        config['DEFAULT']['out_excel_file'] = self.lineEdit.text()
        config['DEFAULT']['filter_excel_file'] = self.lineEdit_2.text()
        if self.checkBox.isChecked():
            config['DEFAULT']['resume_download'] = '1'
        else:
            config['DEFAULT']['resume_download'] = '0'

        with open('config.ini', 'w', encoding='UTF-8') as configfile:
            config.write(configfile)

    def closeEvent(self, event):
        print('closing')
        self.program_exit()

    def adjust_excel_column(self, ws):
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter # Get the column name
            for cell in col:
                try: # Necessary to avoid error on empty cells
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            ws.column_dimensions[column].width = adjusted_width

    def get_naver_keyword(self):
        print('get_naver_keyword')
        clearScreen()
        print_logo(PROGRAM_TITLE, VERSION)
        x = 0
        y = 0
        grid_w = 1200
        grid_h = 800
        download_folder = '.'

        w = WEBManipulator([x,y], [grid_w,grid_h], download_folder, self.lineEdit_7.text(), headless=False)
        
        # https://search.shopping.naver.com/home
        url = 'https://search.shopping.naver.com/search/all?query='
        w.proc_naver(url)

        for i in range(5):
            beepsound()

    def get_coupang_keyword(self):
        # import requests

        # x = requests.get('https://search.shopping.naver.com/api/search/all?adQuery=%ED%99%8D%EC%B0%A8&eq=&iq=&origQuery=%ED%99%8D%EC%B0%A8&pagingIndex=1&pagingSize=40&productSet=checkout&query=%ED%99%8D%EC%B0%A8&sort=rel&viewType=list&window=&xq=')
        # print(x.status_code)

        # return
        print('get_coupang_keyword')
        clearScreen()
        print_logo(PROGRAM_TITLE, VERSION)
        x = 0
        y = 0
        grid_w = 1200
        grid_h = 800
        download_folder = '.'

        w = WEBManipulator([x,y], [grid_w,grid_h], download_folder, int(self.lineEdit_7.text()), headless=False)
        
        url = 'https://www.coupang.com/'
        w.proc_coupang(url)

        # for i in range(5):
        #     beepsound()

    def thread_result_get_all_site(self, s):
        pass
    def thread_complete_get_all_site(self):
        print("THREAD COMPLETE!")
    def progress_fn_get_all_site(self, n):
        print("%d%% done" % n)        

    def get_all_site_thread_run(self):
        print('get_all_site_thread_run')
        # Pass the function to execute
        worker = Worker(self.get_all_site) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.thread_result_get_all_site)
        worker.signals.finished.connect(self.thread_complete_get_all_site)
        worker.signals.progress.connect(self.progress_fn_get_all_site)

        # Execute
        self.threadpool.start(worker)

    def get_out_filename(self, out_path):
        # 날짜_추출키워드_일련번호.xlsx
        from datetime import datetime
        files = os.listdir(out_path)
        file_str = datetime.today().strftime('%Y%m%d')+"_추출키워드_"
        # print(file_str)
        no = 1
        latest = 0
        recent_file = ""
        for file in files:
            print(file)
            if os.path.splitext(file)[1] == ".xlsx":
                ti_m = os.path.getmtime(os.path.join(out_path,file)) # modification time
                if ti_m > latest:
                    latest = ti_m
                    recent_file = file
            if file.startswith(file_str):
                cur_no = int(os.path.splitext(file)[0].replace(file_str, ''))
                if cur_no >= no:
                    no = cur_no + 1
        print([file_str+str(no)+".xlsx", recent_file])
        return [file_str+str(no)+".xlsx", recent_file]


    def get_all_site(self, progress_callback, ret_callback, regMsg_callback):
        print('get_all_site')
        clearScreen()
        print_logo(PROGRAM_TITLE, VERSION)
        x = 0
        y = 0
        grid_w = 1200
        grid_h = 800
        download_folder = '.'

        w = WEBManipulator([x,y], [grid_w,grid_h], download_folder, self.lineEdit_7.text(), headless=False)
        
        self.load_excel()
        [out_filename, recent_filename] = self.get_out_filename(self.lineEdit.text())
        if self.checkBox.isChecked() and recent_filename != "":
            out_filename = recent_filename
            # get last keyword that is already processed in the previous file
            out_filename_full = os.path.join(self.lineEdit.text(), out_filename)
            try:
                df_keyword_processed = pd.read_excel(out_filename_full)
                first_row = len(df_keyword_processed['키워드']) + 2
            except PermissionError as pe:
                workbook = xw.Book(out_filename_full)
                sheet = workbook.sheets.active
                first_row = sheet.range("A1").end("down").row + 2
            print(f'{first_row} 줄부터 시작합니다')
        else:
            first_row = 2

        try:
            w.proc_all_site(self.df_keyword, self.filters, os.path.join(self.lineEdit.text(),out_filename), first_row)
        except Exception as e:
            print(f'에러가 발생했습니다.{e}')
            pass

if __name__ == "__main__":
    app = QApplication()
    w = MainWindow()
    # monitors = QScreen.virtualSiblings(w.screen())
    # print(monitors)
    # monitor = monitors[-1].availableGeometry()
    # # screen = QScreen()
    # # screenGeometry = screen.geometry()
    # height = monitor.height()
    # width = monitor.width()
    # # x=(width - w.width()) / 2.0
    # # y=(height - w.height()) / 2.0
    # x = 100
    # y = 100
    # w.setGeometry(monitor.left() + 100,monitor.top() + 100,w.width(),w.height())
    w.show()
    app.exec()