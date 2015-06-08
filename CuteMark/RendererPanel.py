#!/usr/bin/env python3

# Import PySide classes
import sys, collections, json, tabulate, shutil

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import QWebView
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtNetwork import QNetworkRequest

Signal = pyqtSignal
Slot = pyqtSlot

import matplotlib
matplotlib.use('Agg')


from scilab.tools.project import *
from pathlib import *
# from fn import _ as __
# import formlayout

import scilab
from scilab.expers.configuration import FileStructure
from scilab.graphicaltools.guitesthandler import *
import scilab.graphicaltools.forms as forms
import scilab.datahandling.processingreports 

defaultCss = scilab.datahandling.processingreports.defaultCss 


class MarkdownView(QFrame):
    
    def __init__(self, parent):
        super(TestProtocolView, self).__init__()
        self.parent = parent
        self.setFrameStyle(QFrame.StyledPanel)
        self.htmlView = QWebView()
        
        self.htmlView.setStyle(QStyleFactory.create("windows"))
        
        layout = QVBoxLayout()
        layout.addWidget(self.htmlView)
        self.setLayout(layout)
        
        self.htmlView.page().mainFrame().javaScriptWindowObjectCleared.connect(self.populateJavaScriptWindowObject)
        self.htmlView.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        # view->page()->settings()->setAttribute(QWebSettings::DeveloperExtrasEnabled, true);        

    @Slot()
    def populateJavaScriptWindowObject(self):
        self.htmlView.page().mainFrame().addToJavaScriptWindowObject("formExtractor", self);

    def setHtml(testhtml, testqurl):
        self.htmlView.setHtml(testhtml, testqurl)
        
    @Slot()
    def submit(self):
        
        try:
            print("\n\n[[SUBMIT!!]]\n")
            frame = self.htmlView.page().mainFrame();

            # firstName = frame.findFirstElement("#firstname");
            updatedHtml = frame.toHtml()
            
            with self.protocolTestSampleUrl.open('w', encoding='utf-8') as protocolHtml:
                print("Saving updated protocol: ", str(self.protocolTestSampleUrl))
                protocolHtml.write(updatedHtml)
        
        finally:
            return False

        
    @Slot(object)
    def update(self, obj):
        
        print("TestProtocolView", obj)
        test = self.parent.tester.getitem()
        
        if not test["folder",]:
            self.htmlView.setHtml("<html></html>", QUrl())
            
        else:
            # protocolUrl = test.folder.main / ".." / ".." / 'protocol.html'
            # protocolTestSampleUrl = test.folder.main / 'protocol (test={}).html'.format(test["info"].short)
            
            self.protocolTestSampleUrl = protocolTestSampleUrl
            
            if not protocolUrl.exists() and not protocolTestSampleUrl.exists():
                logging.warn("Protocol doesn't exist for test: "+str(protocolUrl))
                return 
            
            if not protocolTestSampleUrl.exists():
                shutil.copy(str(protocolUrl), str(protocolTestSampleUrl))
                
            with protocolTestSampleUrl.open('rb') as protocolFile:            
                protocolHtmlStr = protocolFile.read().decode(encoding='UTF-8')
                self.htmlView.setHtml(protocolHtmlStr, QUrl("."))            





