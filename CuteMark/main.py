



class TestProtocolView(QFrame):
    
    def __init__(self, parent):
        super(TestProtocolView, self).__init__()
        self.parent = parent
        self.setFrameStyle(QFrame.StyledPanel)
        self.protocolView = QWebView()
        
        self.protocolView.setStyle(QStyleFactory.create("windows"))
        
        layout = QVBoxLayout()
        layout.addWidget(self.protocolView)
        self.setLayout(layout)
        
        self.protocolView.page().mainFrame().javaScriptWindowObjectCleared.connect(self.populateJavaScriptWindowObject)
        self.protocolView.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        # view->page()->settings()->setAttribute(QWebSettings::DeveloperExtrasEnabled, true);
        

    @Slot()
    def populateJavaScriptWindowObject(self):
        self.protocolView.page().mainFrame().addToJavaScriptWindowObject("formExtractor", self);

    def setHtml(testhtml, testqurl):
        self.protocolView.setHtml(testhtml, testqurl)
        
    @Slot()
    def submit(self):
        
        try:
            print("\n\n[[SUBMIT!!]]\n")
            frame = self.protocolView.page().mainFrame();

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
            self.protocolView.setHtml("<html></html>", QUrl())
            
        else:
            protocolUrl = test.folder.main / ".." / ".." / 'protocol.html'
            protocolTestSampleUrl = test.folder.main / 'protocol (test={}).html'.format(test["info"].short)
            
            self.protocolTestSampleUrl = protocolTestSampleUrl
            
            if not protocolUrl.exists() and not protocolTestSampleUrl.exists():
                logging.warn("Protocol doesn't exist for test: "+str(protocolUrl))
                return 
            
            if not protocolTestSampleUrl.exists():
                shutil.copy(str(protocolUrl), str(protocolTestSampleUrl))
                
            with protocolTestSampleUrl.open('rb') as protocolFile:            
                protocolHtmlStr = protocolFile.read().decode(encoding='UTF-8')
                self.protocolView.setHtml(protocolHtmlStr, QUrl("."))            
        