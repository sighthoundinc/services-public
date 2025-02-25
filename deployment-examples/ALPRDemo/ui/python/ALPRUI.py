import wx
import wx.aui
import wx.html2
import requests
import urllib
import json
import io
import os
import argparse
import threading
import time
import subprocess
import cv2
from datetime import datetime
from SIOParser import SIOParser
import argparse

kDefaultTimeout = 5
kDefaultIpAddress = "127.0.0.1"

def epoch_to_offset(epoch_timestamp):
    return datetime.utcfromtimestamp(epoch_timestamp/1000).strftime('%H:%M:%S')

# Function to convert epoch timestamp to string
def epoch_to_string(epoch_timestamp):
    # Convert epoch timestamp to datetime object
    dt = datetime.fromtimestamp(epoch_timestamp/1000)

    # Format the datetime object to a string
    # Change the format string to suit your needs
    return dt.strftime('%Y-%m-%d %H:%M:%S')

class SettingsDialog(wx.Dialog):
    def __init__(self, parent, settings):
        super(SettingsDialog, self).__init__(parent, title="Settings")

        self.settings = settings

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.ip_label = wx.StaticText(self, label="API IP:")
        self.ip_text = wx.TextCtrl(self, value=self.settings["api_ip"])

        self.port_label = wx.StaticText(self, label="API Port:")
        self.port_text = wx.TextCtrl(self, value=self.settings["api_port"])

        self.refresh_rate_label = wx.StaticText(self, label="Refresh Rate (seconds):")
        self.refresh_rate_text = wx.TextCtrl(self, value=str(self.settings["refresh_rate"]))

        self.max_entries_label = wx.StaticText(self, label="Max Entries:")
        self.max_entries_text = wx.TextCtrl(self, value=str(self.settings["max_entries"]))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.save_button = wx.Button(self, label="Save")
        self.cancel_button = wx.Button(self, label="Cancel")

        sizer.Add(self.ip_label, 0, wx.ALL, 5)
        sizer.Add(self.ip_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.port_label, 0, wx.ALL, 5)
        sizer.Add(self.port_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.refresh_rate_label, 0, wx.ALL, 5)
        sizer.Add(self.refresh_rate_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.max_entries_label, 0, wx.ALL, 5)
        sizer.Add(self.max_entries_text, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(self.save_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)


        self.save_button.Bind(wx.EVT_BUTTON, self.onSave)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.onCancel)

        self.SetSizerAndFit(sizer)
        self.Center()

    def onSave(self, event):
        try:
            self.settings["api_ip"] = self.ip_text.GetValue()
            self.settings["api_port"] = self.port_text.GetValue()
            self.settings["refresh_rate"] = int(self.refresh_rate_text.GetValue())
            self.settings["max_entries"] = int(self.max_entries_text.GetValue())
            self.settings["timeout"] = kDefaultTimeout
            self.EndModal(wx.ID_OK)
        except ValueError:
            wx.MessageBox("Please enter valid values for all fields.", "Error", wx.OK | wx.ICON_ERROR)

    def onCancel(self, event):
        self.EndModal(wx.ID_CANCEL)

class MainFrame(wx.Frame):
    # =========================================================================
    def __init__(self, ipAddress, *args, **kw):
        super(MainFrame, self).__init__(*args, **kw)

        self.settings = {
            "api_ip": ipAddress,
            "api_port": "8888",
            "refresh_rate": 10,
            "max_entries": 50,
            "timeout": 10,
        }

        self.data = None
        self.updating = False

        self.initUI()
        self.Center()
        self.startAutoRefresh()
        self.BringToFront()  # Bring the frame to the front

    # =========================================================================
    def initUI(self):
        self.panel = wx.Panel(self)

        # Create the menu bar
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        settings_item = file_menu.Append(wx.ID_ANY, "&Settings", "Open settings dialog")
        exit_item = file_menu.Append(wx.ID_EXIT, "&Exit", "Exit application")
        menu_bar.Append(file_menu, "&File")
        self.SetMenuBar(menu_bar)

        # Bind menu events
        self.Bind(wx.EVT_MENU, self.onSettings, settings_item)
        self.Bind(wx.EVT_MENU, self.onExit, exit_item)

        # Create the notebook with tabs
        self.notebook = wx.Notebook(self.panel)
        self.current_tab = wx.Panel(self.notebook)
        self.search_tab = wx.Panel(self.notebook)
        self.file_tab = wx.Panel(self.notebook)

        self.notebook.AddPage(self.current_tab, "Live Feed")
        self.notebook.AddPage(self.search_tab, "Search Live Feed")
        self.notebook.AddPage(self.file_tab, "File Upload")
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChanged)

        # Layout for the Current tab
        current_sizer = wx.BoxSizer(wx.VERTICAL)
        self.refresh_button = wx.Button(self.current_tab, label="Refresh")
        current_sizer.Add(self.refresh_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.current_tab.SetSizer(current_sizer)

        # Layout for the Search tab
        search_sizer = wx.BoxSizer(wx.VERTICAL)
        self.wildcard_label = wx.StaticText(self.search_tab, label="Search value:")
        self.wildcard_text = wx.TextCtrl(self.search_tab)
        self.date_range_label = wx.StaticText(self.search_tab, label="Date Range (YYYYMMDD or YYYYMMDD-HHMM):")
        self.date_range_start = wx.TextCtrl(self.search_tab)
        self.date_range_end = wx.TextCtrl(self.search_tab)
        self.search_button = wx.Button(self.search_tab, label="Search")
        search_sizer.Add(self.wildcard_label, 0, wx.ALL, 5)
        search_sizer.Add(self.wildcard_text, 0, wx.EXPAND | wx.ALL, 5)
        search_sizer.Add(self.date_range_label, 0, wx.ALL, 5)
        search_sizer.Add(self.date_range_start, 0, wx.EXPAND | wx.ALL, 5)
        search_sizer.Add(self.date_range_end, 0, wx.EXPAND | wx.ALL, 5)
        search_sizer.Add(self.search_button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.search_tab.SetSizer(search_sizer)

        # Layout for the File tab
        file_sizer = wx.BoxSizer(wx.VERTICAL)
        self.uploaded_files_list = wx.ListCtrl(self.file_tab, style=wx.LC_REPORT)
        self.uploaded_files_list.InsertColumn(0, 'File Path')
        self.uploaded_files_list.InsertColumn(1, 'File ID')
        self.uploaded_files_list.InsertColumn(2, 'Status')
        self.uploaded_files_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onFileListItemSelected)
        self.upload_button = wx.Button(self.file_tab, label="Upload ...")
        self.refresh_file_button = wx.Button(self.file_tab, label="Refresh")
        file_sizer.Add(self.uploaded_files_list, 0, wx.EXPAND | wx.ALL, 5)
        file_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        file_button_sizer.Add(self.upload_button, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        file_button_sizer.Add(self.refresh_file_button, 0, wx.ALIGN_LEFT | wx.ALL, 5)
        file_sizer.Add(file_button_sizer)
        self.file_tab.SetSizer(file_sizer)
        self.uploaded_files_results = {}

        self.list_box = self.initListCtrl(self.panel)
        self.image_ctrl = wx.StaticBitmap(self.panel)
        self.lp_ctrl = wx.StaticBitmap(self.panel, size=(200,100))

        # Create a horizontal sizer for image_ctrl and lp_ctrl
        self.image_lp_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.image_lp_sizer.Add(self.image_ctrl, 1, wx.EXPAND | wx.ALL, 5)  # image_ctrl takes more space
        self.image_lp_sizer.Add(self.lp_ctrl, 1, wx.ALIGN_CENTER | wx.ALL, 5)  # lp_ctrl stays small

        # Layout for the main panel
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.notebook, 1, wx.EXPAND)
        main_sizer.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(self.image_lp_sizer, 1, wx.EXPAND | wx.ALL, 5)
        # main_sizer.Add(self.image_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        # main_sizer.Add(self.lp_ctrl, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        self.panel.SetSizer(main_sizer)

        # Bind events
        self.Bind(wx.EVT_BUTTON, self.onRefreshFile, self.refresh_file_button)
        self.Bind(wx.EVT_BUTTON, self.onRefreshCurrent, self.refresh_button)
        self.Bind(wx.EVT_BUTTON, self.onSearch, self.search_button)
        self.Bind(wx.EVT_BUTTON, self.onUpload, self.upload_button)


    # =========================================================================
    def onUpload(self,event):
        with wx.FileDialog(self.panel, "Choose a file to upload", wildcard="*.*",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return  # User cancelled the operation

            # Get the selected file path
            filepath = file_dialog.GetPath()

            # Only upload each file once
            item_count = self.uploaded_files_list.GetItemCount()
            for i in range(item_count):
                item_text = self.uploaded_files_list.GetItemText(i)
                if item_text == filepath:
                    wx.MessageBox(f"File {filepath} already has been uploaded", "Error", wx.OK | wx.ICON_ERROR)
                    return

            # Perform the file upload (here you can adjust the URL and parameters)
            try:
                with open(filepath, 'rb') as f:
                    files = {'file': (os.path.basename(filepath), f)}
                    uri = f"{self.apiRoot()}/folderwatch/upload/us"

                    response = requests.post(uri, files=files, timeout=self.settings['timeout'])

                    # Check response status
                    if response.status_code != 200:
                        wx.MessageBox(f"An error occurred: {response.reason}", "Error", wx.OK | wx.ICON_ERROR)
                        return

                    id = response.json().get('id', None)
                    if id is None:
                        wx.MessageBox(f"An error occurred: {response.reason}", "Error", wx.OK | wx.ICON_ERROR)
                        return

                    idx = self.uploaded_files_list.GetItemCount()
                    self.uploaded_files_list.InsertItem(idx, filepath)
                    self.uploaded_files_list.SetItem(idx, 1, id)
                    self.uploaded_files_list.SetItem(idx, 2, "Uploaded")
            except requests.exceptions.ConnectionError:
                self.handleTimeout()
            except requests.Timeout:
                self.handleTimeout()
            except Exception as e:
                wx.MessageBox(f"An error occurred: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    # =========================================================================
    def handleTimeout(self):
        result = wx.MessageBox(f"Timeout reached communicating to {self.settings['api_ip']}. Do you want to modify settings?", "Update settings?", wx.YES_NO | wx.ICON_QUESTION)

        # Check the response
        if result == wx.YES:
            shouldStart = self.auto_refresh
            self.stopAutoRefresh()
            self.onSettings(None)
            if shouldStart:
                self.startAutoRefresh()

    # =========================================================================
    def onTabChanged(self,event):
        self.clearSharedUIState()

    # =========================================================================
    def clearSharedUIState(self):
        self.list_box.DeleteAllItems()
        self.clearImage(self.image_ctrl)
        self.clearImage(self.lp_ctrl)
        self.panel.Layout()

    # =========================================================================
    def initListCtrl(self,parent):
        ctrl = wx.ListCtrl(parent, style=wx.LC_REPORT)
        ctrl.InsertColumn(0, 'Time')
        ctrl.InsertColumn(1, 'Make/Model/Color')
        ctrl.InsertColumn(2, 'Plate/State')
        ctrl.InsertColumn(3, 'Source')
        ctrl.InsertColumn(4, 'UID')
        # Bind the single-click event
        ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onListItemSelected)
        return ctrl

    # =========================================================================
    def clearImage(self, ctrl):
        size = ctrl.GetSize()
        empty_image = wx.Image(*size)
        empty_bitmap = wx.Bitmap(empty_image)
        ctrl.SetBitmap(empty_bitmap)

    # =========================================================================
    def renderImage(self, ctrl, srcImage):
        # Get the size of the static bitmap control
        size = ctrl.GetSize()
        # Calculate the aspect ratio of the original image
        aspectRatio = float(srcImage.GetWidth()) / float(srcImage.GetHeight())
        # Calculate the new width and height to fit the image within the available space
        newWidth = min(size[0], int(size[1] * aspectRatio))
        newHeight = min(size[1], int(newWidth / aspectRatio))
        # Scale the image to fit the size of the control
        renderedImage = srcImage.Scale(newWidth, newHeight, wx.IMAGE_QUALITY_HIGH)
        # Convert wx.Image to wx.Bitmap
        bitmap = wx.Bitmap(renderedImage)

        # Set the wx.StaticBitmap with the loaded image
        ctrl.SetBitmap(bitmap)
        ctrl.Refresh()
        self.panel.Layout()

    # =========================================================================
    def updateImage(self, content, type, box):
        #
        # Handle rendered image resize
        #


        # Check the Content-Type and initialize wx.Image accordingly
        if 'image/jpeg' in type:
            t = wx.BITMAP_TYPE_JPEG
        elif 'image/png' in type:
            t = wx.BITMAP_TYPE_PNG
        elif 'image/gif' in type:
            t = wx.BITMAP_TYPE_GIF
        else:
            print(f"CT is {type}")
            t = wx.BITMAP_TYPE_JPEG

        srcImage = wx.Image(io.BytesIO(content), t)
        self.renderImage(self.image_ctrl, srcImage)

        crop = srcImage.GetSubImage(box)
        self.renderImage(self.lp_ctrl, crop)


    # =========================================================================
    def onFileListItemSelected(self,event):
        self.clearSharedUIState()

        list = event.GetEventObject()
        index = event.GetIndex()
        filename = self.uploaded_files_list.GetItemText(index)
        msg = self.uploaded_files_results.get(filename, None)
        if not msg is None:
            parser = SIOParser()
            parser.parseSIOResult(msg)
            self.data = parser.getLPs()
            self.populateListWithData(self.data, self.list_box, True)

    # =========================================================================
    def onListItemSelected(self,event):
        index = event.GetIndex()

        if self.notebook.GetSelection() == 2:
            self.populateLocalFrame(index)
        else:
            self.populateRemoteFrame(index)

    # =========================================================================
    def populateLocalFrame(self, index):
        index = self.uploaded_files_list.GetFirstSelected()
        if index < 0:
            return
        filename = self.uploaded_files_list.GetItemText(index)

        lpIdx = self.list_box.GetFirstSelected()
        lp = self.data[lpIdx]
        offset = lp['frameid']
        box = lp['box']

        print(f"populateLocalFrame: lp={lp}")
        frame = self.getFrame(filename, offset)
        if not frame:
            return

        self.renderImage(self.image_ctrl, frame)

        crop = frame.GetSubImage(box)
        self.renderImage(self.lp_ctrl, crop)



    # =========================================================================
    def getFrame(self, filename, frame_pos):
        """
        Extracts a frame from a video file at the specified offset in seconds.

        :param filename: The path to the video file.
        :param offset_seconds: The time offset in seconds where the frame is extracted.
        :return: The extracted frame as an image, or None if it fails.
        """

        # Open the video file
        video_capture = cv2.VideoCapture(filename)

        # Get frames per second (FPS) to calculate frame position
        ext = os.path.splitext(filename)[1]

        # Set the video capture to the specific frame position
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)

        # Read the frame
        success, npframe = video_capture.read()

        # Release the video capture object
        video_capture.release()

        if success:
            # Convert BGR to RGB if using OpenCV
            if len(npframe.shape) == 3 and npframe.shape[2] == 3:
                npframe = cv2.cvtColor(npframe, cv2.COLOR_BGR2RGB)

            height, width = npframe.shape[:2]

            # Convert the numpy array to a wx.Image
            wx_image = wx.Image(width, height, npframe)
            return wx_image
        else:
            print(f"Error: Could not read the frame at the specified time {offset_seconds} and fps {fps}.")
            return None


    # =========================================================================
    def populateRemoteFrame(self, index):
        id = self.data[index]["imageId"]
        src = self.data[index]["sourceId"]
        box = self.data[index]["rect"]

        uri = f"{self.apiRoot()}/plates/image/{src}"
        try:
            response = requests.get(uri, params={'id':id}, timeout=self.settings['timeout'])
            if response.status_code != 200:
                raise Exception(f"Error {response.status_code} retrieving latest results from {uri}")
            self.updateImage(response.content, response.headers['Content-Type'], box)
        except requests.exceptions.ConnectionError:
            self.handleTimeout()
        except requests.Timeout:
            self.handleTimeout()
        except Exception as e:
            print(f"Error updating image contents: {e}")
            self.clearImage(self.image_ctrl)
            self.clearImage(self.lp_ctrl)

    # =========================================================================
    def onSettings(self, event):
        dlg = SettingsDialog(self, self.settings)
        if dlg.ShowModal() == wx.ID_OK:
            self.updateSettings()
        dlg.Destroy()

    # =========================================================================
    def onExit(self, event):
        self.stopAutoRefresh()
        self.Destroy()

    # =========================================================================
    def updateSettings(self):
        self.stopAutoRefresh()
        self.startAutoRefresh()

    # =========================================================================
    def startAutoRefresh(self):
        self.auto_refresh = True
        self.refresh_thread = threading.Thread(target=self.autoRefresh)
        self.refresh_thread.start()

    # =========================================================================
    def stopAutoRefresh(self):
        self.auto_refresh = False
        self.refresh_thread.join()

    # =========================================================================
    def autoRefresh(self):
        while self.auto_refresh:
            if self.notebook.GetSelection() == 0:
                wx.CallAfter(self.updateCurrentTab)
            elif self.notebook.GetSelection() == 2:
                wx.CallAfter(self.updateFileTab)
            time.sleep(self.settings["refresh_rate"])

    # =========================================================================
    def populateListWithData(self,data,ctrl,isoffset):
        ctrl.DeleteAllItems()
        index = 0
        for entry in data:
            # {'oid': 'rtsp-stream-2-lp-298-1724884952043', 'rect': [203, 279, 58, 39], 'region': 'Florida', 'sourceId': 'rtsp-stream-2', 'string': 'HPP8X', 'time': 1724885848430},
            if isoffset:
                dt = epoch_to_offset(int(entry['time']))
            else:
                dt = epoch_to_string(int(entry['time']))
            ctrl.InsertItem(index, f"{dt}")
            ctrl.SetItem(index, 1, f"{entry['make']}/{entry['model']}/{entry['color']}")
            ctrl.SetItem(index, 2, f"{entry['string']}/{entry['region']}")
            ctrl.SetItem(index, 3, f"{entry['sourceId']}")
            ctrl.SetItem(index, 4, f"{entry['oid']}")
            index = index + 1

            for i in range(4):  # Adjust all columns
                ctrl.SetColumnWidth(i, wx.LIST_AUTOSIZE)

    # =========================================================================
    def apiRoot(self):
        return f"http://{self.settings['api_ip']}:{self.settings['api_port']}"

    # =========================================================================
    def updateFileTab(self):
        if self.updating:
            return
        self.updating = True
        item_count = self.uploaded_files_list.GetItemCount()
        for i in range(item_count):
            item_file = self.uploaded_files_list.GetItemText(i)
            item_id = self.uploaded_files_list.GetItemText(i,1)
            item_status = self.uploaded_files_list.GetItemText(i,2)

            # if item_status in [ "error", "completed" ]:
            #     continue

            if not os.path.isfile(item_file):
                self.uploaded_files_list.SetItem(i,2,"missing")
                continue

            uri = f"{self.apiRoot()}/folderwatch/status/{item_id}"

            try:
                response = requests.get(uri, timeout=self.settings['timeout'])
            except requests.exceptions.ConnectionError:
                self.handleTimeout()
            except requests.Timeout:
                self.handleTimeout()
                response = None


            # Check response status
            if not response or response.status_code != 200:
                self.uploaded_files_list.SetItem(i,2,"error")
                continue

            j = response.json()
            status = j.get("status", "error")
            self.uploaded_files_list.SetItem(i,2,status)

            if status == "completed":
                result = j.get("result","")
                self.uploaded_files_results[item_file] = result
        self.updating = False



    # =========================================================================
    def updateCurrentTab(self):
        if self.updating:
            return
        self.updating = True
        try:
            response = requests.get(f"{self.apiRoot()}/plates/latest/{self.settings['max_entries']}",
                                    timeout=self.settings['timeout'])
            if response.status_code != 200:
                raise Exception(f"Error {response.status_code} retrieving latest results")
            self.data = response.json()
            self.populateListWithData(self.data, self.list_box, False)
        except requests.exceptions.ConnectionError:
            self.handleTimeout()
        except requests.Timeout:
            self.handleTimeout()
        except Exception as e:
            print(f"Error updating current tab: {e}")
        self.updating = False

    # =========================================================================
    def onRefreshCurrent(self, event):
        if self.notebook.GetSelection() == 0:
            self.updateCurrentTab()

    # =========================================================================
    def onRefreshFile(self, event):
        if self.notebook.GetSelection() == 2:
            self.updateFileTab()

    # =========================================================================
    def validateDateTime(self,ctrl,name):
        dt = ctrl.GetValue()
        if len(dt):
            dtTuple = dt.split('-')
            if len(dtTuple) == 1 and len(dtTuple[0]) == 8:
                dt = dtTuple[0] + "/0000"
            elif len(dtTuple) == 2 and len(dtTuple[0]) == 8 and len(dtTuple[1]) == 4:
                dt = dtTuple[0] + "/" + dtTuple[1]
            else:
                raise Exception(f"Please use YYYYMMDD-HHMM or YYYYMMDD for {name} date")
        return dt

    # =========================================================================
    def onSearch(self, event):
        # Implement search functionality here
        searchTerm = self.wildcard_text.GetValue()
        if (len(searchTerm)):
            verb = "search"
            params={'plate':searchTerm}
        else:
            verb = "bytimeanddate"
            params = {}
        try:
            start = self.validateDateTime(self.date_range_start,"start")
            end = self.validateDateTime(self.date_range_end,"end")
        except Exception as e:
            wx.MessageBox(str(e), "Error", wx.OK | wx.ICON_ERROR)
            return
        uri = f"{self.apiRoot()}/plates/{verb}"
        if start:
            uri = uri + f"/{start}"
        if end:
            uri = uri + f"/{end}"
        try:
            response = requests.get(uri, params=params, timeout=self.settings['timeout'])
            if response.status_code != 200:
                raise Exception(f"Error {response.status_code} retrieving search results")
            self.data = response.json()
            self.populateListWithData(self.data, self.list_box, False)
        except requests.exceptions.ConnectionError:
            self.handleTimeout()
        except requests.Timeout:
            self.handleTimeout()
        except Exception as e:
            wx.MessageBox(f"Error updating search tab: {e}", "Error", wx.OK | wx.ICON_ERROR)

    # =========================================================================
    def onClose(self, event):
        self.stopAutoRefresh()
        self.Destroy()

    # =========================================================================
    # Bring the app to front
    def BringToFront(self):
        if wx.Platform == "__WXMAC__":
            try:
                script = 'tell application "System Events" to set frontmost of process "Python" to true'
                subprocess.call(['osascript', '-e', script])
            except Exception as e:
                print("Error bringing window to front:", e)


def main():

    # Load args
    parser = argparse.ArgumentParser(description='Run ALPR Demo Client UI')
    parser.add_argument('-i', '--ipAddress', type=str, help='The Server IP Address', default=kDefaultIpAddress)

    args = parser.parse_args()
    ipAddress = args.ipAddress

    app = wx.App(False)
    frame = MainFrame(ipAddress, None, title="ALPR Demo", size=(800, 600))
    frame.Bind(wx.EVT_CLOSE, frame.onClose)
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
