#-------------------------------------------------------------------------------
# Name:        Go board recognition project
# Purpose:     Main functions
#
# Author:      skolchin
#
# Created:     04.07.2019
# Copyright:   (c) skolchin 2019
#-------------------------------------------------------------------------------
import numpy as np
import cv2
import os
import sys
from PIL import Image, ImageTk
from pathlib import Path
import xml.dom.minidom as minidom
from gr.utils import img_to_imgtk, resize2
from gbr import GbrGUI
from view_anno import ViewAnnoGui
import re
from gr.ui_extra import treeview_sort_columns

if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk
else:
    import tkinter as tk
    from tkinter import ttk

# GUI class
class GrTagGui:
      def __init__(self, root):
          self.root = root

          # Set paths
          self.root_path = Path(__file__).parent.resolve()
          self.src_path = self.root_path.joinpath("img")
          self.ds_path = self.root_path.joinpath("gbr_ds")
          if not self.ds_path.exists(): self.ds_path.mkdir(parents = True)
          self.meta_path = self.ds_path.joinpath("data","Annotations")
          if not self.meta_path.exists(): self.meta_path.mkdir(parents = True)
          self.img_path = self.ds_path.joinpath("data","Images")
          if not self.img_path.exists(): self.img_path.mkdir(parents = True)

          # File list panel
          self.filesFrame = tk.Frame(self.root)
          self.filesFrame.pack(side = tk.LEFT, fill=tk.BOTH, expand = False)

          # Notebook panel
          self.nbFrame = tk.Frame(self.root)
          self.nbFrame.pack(side = tk.LEFT, fill=tk.BOTH, expand = True)

          # Files table
          self.fileListSb = tk.Scrollbar(self.filesFrame)
          self.fileListSb.pack(side=tk.RIGHT, fill=tk.BOTH)

          self.fileList = ttk.Treeview(self.filesFrame, height = 30)
          self.fileList["columns"]=("json","jgf", "ds")
          self.fileList.column("#0", width=150, minwidth=50, stretch=tk.YES)
          self.fileList.column("json", width=50, minwidth=30, stretch=tk.YES)
          self.fileList.column("jgf", width=50, minwidth=30, stretch=tk.YES)
          self.fileList.column("ds", width=50, minwidth=30, stretch=tk.YES)
          self.fileList.heading("#0",text="Name",anchor=tk.W)
          self.fileList.heading("json", text="JSON",anchor=tk.W)
          self.fileList.heading("jgf", text="JGF",anchor=tk.W)
          self.fileList.heading("ds", text="DS",anchor=tk.W)
          #treeview_sort_columns(self.fileList)

          self.load_files()

          self.fileList.pack(side = tk.TOP, fill=tk.BOTH, expand = True)
          self.fileList.bind("<<TreeviewSelect>>", self.sel_changed_callback)
          self.fileListSb.config(command=self.fileList.yview)

          # Notebook
          self.nb = ttk.Notebook(self.nbFrame)
          self.nb.pack(side = tk.TOP, fill=tk.BOTH, expand = True)
          self.nb.bind("<<NotebookTabChanged>>", self.sel_changed_callback)

          # GBR GUI
          self.nbFrameTag = tk.Frame(self.nb, width = 400)
          self.nb.add(self.nbFrameTag, text = "Tagging")
          self.grGui = GbrGUI(self.nbFrameTag, max_img_size = 400, max_dbg_img_size = 150, allow_open = False)

          # ANNO GUI
          self.nbFrameAnno = tk.Frame(self.nb, width = 400)
          self.nb.add(self.nbFrameAnno, text = "Annotation")
          self.annoGui = ViewAnnoGui(self.nbFrameAnno, allow_open = False)

      def _add_file(self, file_name, file_list):
          file_state = [ \
                     [file_name.with_suffix('.json'), "-", 0],
                     [file_name.with_suffix('.jgf'), "-", 0],
                     [self.meta_path.joinpath(file_name.name).with_suffix('.xml'), "-", 0] ]

          # Load file info
          for f in file_state:
            fn = str(f[0])
            if os.path.isfile(fn):
                m = os.path.getmtime(fn)
                f[1] = "+"
                f[2] = m

          # Check dependencies
          prev_mt = os.path.getmtime(str(file_name))
          for f in file_state:
              if f[2] > 0:
                 if f[2] < prev_mt: f[1] = '<'
                 prev_mt = f[2]

          # Add to file list
          values = [f[1] for f in file_state]
          file_list[file_name.name] = values

      def load_files(self):
          file_list = dict()
          for ext in ('*.png', '*.jpg'):
              g = self.src_path.glob(ext)
              for x in g:
                  if x.is_file(): self._add_file(x, file_list)

          def _sort_key(f):
              r = re.search(r"\d+", f)
              if r is None: return 0
              else: return int(r.group())

          for f in sorted(file_list.keys(), key = _sort_key):
              self.fileList.insert("", "end", text = f, values=file_list[f])

      def sel_changed_callback(self, event):
          sel = self.fileList.selection()
          if len(sel) == 0: return

          item = self.fileList.item(sel)
          file = item['text']
          nb_index = self.nb.index(self.nb.select())
          if nb_index == 0:
            file = self.src_path.joinpath(file)
            self.grGui.load_image(str(file))
          else:
            file = self.meta_path.joinpath(file).with_suffix('.xml')
            self.annoGui.load_annotation(str(file))

def main():
    window = tk.Tk()
    window.title("Go tagging")

    gui = GrTagGui(window)

    #window.grid_columnconfigure(0, weight=1)
    #window.grid_rowconfigure(0, weight=1)
    #window.resizable(True, True)

    # Main loop
    window.mainloop()

    # Clean up
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
