#-------------------------------------------------------------------------------
# Name:        Go board recognition project
# Purpose:     Main and interfaces functions
#
# Author:      skolchin
#
# Created:     04.07.2019
# Copyright:   (c) skolchin 2019
#-------------------------------------------------------------------------------

from gr.grdef import *
from gr.gr import *
from gr.utils import img_to_imgtk

import numpy as np
import cv2
import sys

from PIL import Image, ImageTk
import json
from pathlib import Path

if sys.version_info[0] < 3:
    import Tkinter as tk
    import tkFileDialog  as filedialog
    import ttk
else:
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import ttk


# Constants
PADX = 5
PADY = 5

# Image frame with additional tag - for debug info
class NLabel(tk.Label):
      def __init__(self, master, tag=None, *args, **kwargs):
          tk.Label.__init__(self, master, *args, **kwargs)
          self.master, self.tag = master, tag


# GUI class
class GbrGUI:
      MAX_IMG_SIZE = 550
      MAX_DBG_IMG_SIZE = 200

      def __init__(self, root):
          self.root = root

          # Defaults params
          self.grParams = DEF_GR_PARAMS.copy()
          self.grRes = None
          self.showBlack = True
          self.showWhite = True
          self.showBoxes = False

          # Default board image and generated image
          self.origImg = generate_board()
          self.origImgName = None
          self.origImgTk, self.zoom = self.make_imgtk(self.origImg)
          self.genImg = self.origImg
          self.genImgTk, _ = self.make_imgtk(self.genImg)

          # Images panel (original + generated + analysis)
          self.imgFrame = tk.Frame(self.root)
          self.imgFrame.grid(row = 0, column = 0, padx = PADX, pady = PADY)

          # Image panel: original image (label + photo)
          self.origImgLabel = tk.Label(self.imgFrame, text = "Original")
          self.origImgLabel.grid(row = 0, column = 0, sticky = "nswe")

          self.origImgPanel = tk.Label(self.imgFrame, image = self.origImgTk)
          self.origImgPanel.bind('<Button-1>', self.orig_img_mouse_callback)
          self.origImgPanel.grid(row = 1, column = 0, sticky = "nswe", padx = PADX)

          # Image panel: generated image header
          self.genLblFrame = tk.Frame(self.imgFrame)
          self.genLblFrame.grid(row = 0, column = 1, sticky = "nswe")
          tk.Grid.columnconfigure(self.genLblFrame, 0, weight = 1)

          # Image panel: generated image header: label + buttons
          self.genImgLabel = tk.Label(self.genLblFrame, text = "Generated")
          self.genImgLabel.grid(row = 0, column = 0, padx = PADX, pady = PADY, sticky = "nswe")

          self.blackImgTk = [ImageTk.PhotoImage(Image.open('black_up.png')),
                             ImageTk.PhotoImage(Image.open('black_down.png'))]
          self.showBlackBtn = tk.Label(self.genLblFrame, image = self.blackImgTk[1],
                                                         borderwidth = 1,
                                                         relief = "groove",
                                                         width = 30)
          self.showBlackBtn.bind("<Button-1>", self.show_black_callback)
          self.showBlackBtn.grid(row = 0, column = 1, padx = PADX, pady = PADY, sticky = "nswe")

          self.whiteImgTk = [ImageTk.PhotoImage(Image.open('white_up.png')),
                             ImageTk.PhotoImage(Image.open('white_down.png'))]
          self.showWhiteBtn = tk.Label(self.genLblFrame, image = self.whiteImgTk[1],
                                                         borderwidth = 1,
                                                         relief = "groove",
                                                         width = 30)
          self.showWhiteBtn.bind("<Button-1>", self.show_white_callback)
          self.showWhiteBtn.grid(row = 0, column = 2, padx = PADX, pady = PADY, sticky = "nswe")

          self.boxImgTk = [ImageTk.PhotoImage(Image.open('box_up.png')),
                           ImageTk.PhotoImage(Image.open('box_down.png'))]
          self.showBoxBtn = tk.Label(self.genLblFrame, image = self.boxImgTk[0],
                                                         borderwidth = 1,
                                                         relief = "groove",
                                                         width = 30)
          self.showBoxBtn.bind("<Button-1>", self.show_boxes_callback)
          self.showBoxBtn.grid(row = 0, column = 3, padx = PADX, pady = PADY, sticky = "nswe")

          # Image panel: generated image panel
          self.genImgPanel = tk.Label(self.imgFrame, image = self.origImgTk)
          self.genImgPanel.bind('<Button-1>', self.gen_img_mouse_callback)
          self.genImgPanel.grid(row = 1, column = 1, sticky = "nswe", padx = PADX)

          # Image panel: analysis images
          self.dbgImgLabel = tk.Label(self.imgFrame, text = "Analysis")
          self.dbgImgLabel.grid(row = 0, column = 2, sticky = "nwe")

          self.dbgFrameRoot = tk.Frame(self.imgFrame)
          self.dbgFrameRoot.grid(row = 1, column = 2, padx = PADX, sticky = "nswe")

          self.dbgFrameCanvas = tk.Canvas(self.dbgFrameRoot)
          self.dbgFrameCanvas.pack(side = tk.LEFT)
          self.dbgFrameScrollY = tk.Scrollbar(self.dbgFrameRoot, command=self.dbgFrameCanvas.yview)
          self.dbgFrameScrollY.pack(side=tk.LEFT, fill='y')

          self.dbgFrameCanvas.configure(yscrollcommand = self.dbgFrameScrollY.set)
          self.dbgFrameCanvas.bind('<Configure>', self.on_scroll_configure)

          self.dbgFrame = tk.Frame(self.dbgFrameCanvas)
          self.dbgFrameCanvas.create_window((0,0), window=self.dbgFrame, anchor='nw')

          # Info frame
          self.infoFrame = tk.Frame(self.root, width = self.origImg.shape[CV_WIDTH]*2, height = 300)
          self.infoFrame.grid(row = 1, column = 0, padx = PADX, pady = PADY, sticky = "nswe")

          # Info frame: buttons
          self.buttonFrame = tk.Frame(self.infoFrame, bd = 1, relief = tk.RAISED,
                                                 width = self.origImg.shape[CV_WIDTH]*2+PADX*2, height = 50)
          self.buttonFrame.grid(row = 0, column = 0, sticky = "nswe")
          self.buttonFrame.grid_propagate(0)

          self.loadImgBtn = tk.Button(self.buttonFrame, text = "Load image",
                                                        command = self.load_img_callback)
          self.loadImgBtn.grid(row = 0, column = 0, padx = PADX, pady = PADY)

          self.saveParamBtn = tk.Button(self.buttonFrame, text = "Save params",
                                                          command = self.save_json_callback)
          self.saveParamBtn.grid(row = 0, column = 1, padx = PADX, pady = PADY)

          self.saveBrdBtn = tk.Button(self.buttonFrame, text = "Save board",
                                                        command = self.save_jgf_callback)
          self.saveBrdBtn.grid(row = 0, column = 2, padx = PADX, pady = PADY)

          self.applyBtn = tk.Button(self.buttonFrame, text = "Apply",
                                                      command = self.apply_callback)
          self.applyBtn.grid(row = 0, column = 3, padx = PADX, pady = PADY)

          self.applyDefBtn = tk.Button(self.buttonFrame, text = "Defaults",
                                                         command = self.apply_def_callback)
          self.applyDefBtn.grid(row = 0, column = 4, padx = PADX, pady = PADY)

          # Info frame: stones info
          self.boardInfo = tk.StringVar()
          self.boardInfo.set("No stones found")
          self.boardInfoPanel = tk.Label(self.buttonFrame, textvariable = self.boardInfo)
          self.boardInfoPanel.grid(row = 0, column = 5, sticky = "nwse", padx = PADX)

          # Info frame: switches
          self.switchFrame = tk.Frame(self.infoFrame, bd = 1, relief = tk.RAISED)
          self.switchFrame.grid(row = 1, column = 0, sticky = "nswe")
          self.tkVars = self.add_switches(self.switchFrame, self.grParams)

          # Status bar
          self.statusFrame = tk.Frame(self.root, width = 200, bd = 1, relief = tk.SUNKEN)
          self.statusFrame.grid(row = 2, column = 0, sticky = "nswe")

          self.stoneInfo = tk.StringVar()
          self.stoneInfo.set("")
          self.stoneInfoPanel = tk.Label(self.statusFrame, textvariable = self.stoneInfo)
          self.stoneInfoPanel.grid(row = 0, column = 0, sticky = tk.W, padx = 5, pady = 2)


      # Callback functions
      # Callback for mouse events on generated board image
      def gen_img_mouse_callback(self, event):
          # Convert from widget coordinates to image coordinates
          w = event.widget.winfo_width()
          h = event.widget.winfo_height()
          x = event.x
          y = event.y
          zx = self.zoom[GR_X]
          zy = self.zoom[GR_Y]

          if self.origImgName is None:
            return

          x = int((x - (w - self.origImg.shape[CV_WIDTH] * zx) / 2) / zx)
          y = int((y - (h - self.origImg.shape[CV_HEIGTH] * zy) / 2) / zy)
          print('{}, {}'.format(x, y))

          f = "Black"
          p = find_coord(x, y, self.grRes[GR_STONES_B])
          if (p[0] == -1):
            f = "White"
            p = find_coord(x, y, self.grRes[GR_STONES_W])
          if (p[0] >= 0):
            ct = "{f} {a}{b} at ({x},{y}):{r}".format(
               f = f,
               a = stone_pos(p, GR_A),
               b = stone_pos(p, GR_B),
               x = round(p[GR_X],0),
               y = round(p[GR_Y],0),
               r = round(p[GR_R],0))
            print(ct)
            self.stoneInfo.set(ct)

      # Callback for mouse events on original image
      def orig_img_mouse_callback(self, event):
          self.load_img_callback()

      # Callback for mouse event on debug image
      def dbg_img_mouse_callback(self, event):
        w = event.widget
        k = w.tag
        show(k, self.grRes[k])

      # Load image button callback
      def load_img_callback(self):
        fn = filedialog.askopenfilename(title = "Select file",
           filetypes = (("PNG files","*.png"),("JPEG files","*.jpg"),("All files","*.*")))
        if (fn != ""):
           # Load the image
           self.origImg = cv2.imread(fn)
           self.origImgTk, self.zoom = self.make_imgtk(self.origImg)
           self.origImgPanel.configure(image = self.origImgTk)
           self.origImgName = fn

           # Load JSON with image recog parameters
           ftitle = ""
           fnj = Path(self.origImgName).with_suffix('.json')
           if fnj.is_file():
              p = json.load(open(str(fnj)))
              ftitle = " (with params)"
              for key in self.grParams.keys():
                  if p.get(key) is not None:
                     self.grParams[key] = p[key]
                     if key in self.tkVars:
                        self.tkVars[key].set(self.grParams[key])

           # Process image
           self.showBlack = True
           self.showWhite = True
           self.showBoxes = False
           self.update_board(reprocess = True)

           # Update status
           self.stoneInfo.set("File loaded{ft}: {fn}".format(ft = ftitle, fn = str(self.origImgName)))

      # Save params button callback
      def save_json_callback(self):
        # Save json with current parsing parameters
        if self.origImgName is None:
           # Nothing to do!
           return

        fn = Path(self.origImgName).with_suffix('.json')
        with open(str(fn), "w", encoding="utf-8", newline='\r\n') as f:
             json.dump(self.grParams, f, indent=4, sort_keys=True, ensure_ascii=False)

        self.stoneInfo.set("Params saved to: " + str(fn))

      # Save stones button callback
      def save_jgf_callback(self):
        # Save json with current parsing parameters
        if self.origImgName is None:
           # Nothing to do!
           return

        jgf = gres_to_jgf(self.grRes)
        jgf['image_file'] = self.origImgName

        fn = Path(self.origImgName).with_suffix('.jgf')
        with open(fn, "w", encoding="utf-8", newline='\r\n') as f:
             json.dump(jgf, f, indent=4, sort_keys=True, ensure_ascii=False)

        self.stoneInfo.set("Board saved to: " + str(fn))

      # Apply button callback
      def apply_callback(self):
        for key in self.tkVars.keys():
            self.grParams[key] = self.tkVars[key].get()
        self.update_board(reprocess = True)

      # Apply defaults button callback
      def apply_def_callback(self):
        self.grParams = DEF_GR_PARAMS.copy()
        for key in self.tkVars.keys():
            self.tkVars[key].set(self.grParams[key])
        self.update_board(reprocess = True)

      # Callback for canvas configuration
      def on_scroll_configure(self, event):
        # update scrollregion after starting 'mainloop'
        # when all widgets are in canvas
        self.dbgFrameCanvas.configure(scrollregion=self.dbgFrameCanvas.bbox('all'))

      # Callback for "Show black stones"
      def show_black_callback(self, event):
        if self.origImgName is None:
           return

        self.showBlack = not self.showBlack
        self.showBlackBtn.configure(image = self.blackImgTk[int(self.showBlack)])
        self.update_board(reprocess= False)

      # Callback for "Show white stones"
      def show_white_callback(self, event):
        if self.origImgName is None:
           return

        self.showWhite = not self.showWhite
        self.showWhiteBtn.configure(image = self.whiteImgTk[int(self.showWhite)])
        self.update_board(reprocess= False)

      # Callback for "Show boxes"
      def show_boxes_callback(self, event):
        if self.origImgName is None:
           return

        self.showBoxes = not self.showBoxes
        self.showBoxBtn.configure(image = self.boxImgTk[int(self.showBoxes)])
        self.update_board(reprocess= False)

      # Add Scale widgets with board recognition parameters
      def add_switches(self, rootFrame, params, nrow = 0):
        n = 1
        ncol = 0
        frame = None
        vars = dict()

        # Add a tabbed notebook
        nb = ttk.Notebook(rootFrame)
        nb.grid(row = nrow, column = 0, sticky = "nswe", padx = PADX, pady = PADY)

        # Get unique tabs
        tabs = set([e[2] for e in GR_PARAMS_PROP.values() if e[2]])

        # Add switches to notebook tabs
        for tab in sorted(tabs):
            # Add a tab frame
            nbFrame = tk.Frame(nb, width = 400)
            nb.add(nbFrame, text = tab)
            frame = None
            n = 0
            ncol = 0

            # Iterate through the params processing only ones belonging to current tab
            for key in params.keys():
                if GR_PARAMS_PROP[key][2] == tab:
                    if (n == 3 or frame is None):
                       frame = tk.Frame(nbFrame, width = 400)
                       frame.grid(row = 0, column = ncol, padx = 3, pady = 3)
                       n = 0
                       ncol = ncol + 1

                    # Add a switch
                    panel = tk.Label(frame, text = key)
                    panel.grid(row = n, column = 0, padx = 2, pady = 2, sticky = "s")

                    v = tk.IntVar()
                    v.set(params[key])
                    panel = tk.Scale(frame, from_ = GR_PARAMS_PROP[key][0],
                                            to = GR_PARAMS_PROP[key][1],
                                            orient = tk.HORIZONTAL,
                                            variable = v)
                    panel.grid(row = n, column = 1, padx = 2, pady = 2)
                    vars[key] = v

                    n = n + 1
        return vars

      # Add analysis results info
      def add_debug_info(self, root, shape, res):
        if res is None:
           return

        nrow = 0
        ncol = 0
        sx = int(shape[CV_WIDTH] / 2) - 5
        if sx > self.MAX_DBG_IMG_SIZE: sx = self.MAX_DBG_IMG_SIZE
        sy = int(float(sx) / float(shape[CV_WIDTH]) * shape[CV_HEIGTH])

        # Remove all previously added controls
        for c in root.winfo_children():
            c.destroy()

        # Add analysis result images
        for key in res.keys():
            if key.find("IMG_") >= 0:
               frame = tk.Frame(root)
               frame.grid(row = nrow, column = ncol, padx = 2, pady = 2, sticky = "nswe")

               img = cv2.resize(res[key], (sx, sy))

               imgtk = ImageTk.PhotoImage(image=Image.fromarray(img))
               panel = NLabel(frame, image = imgtk, tag = key)
               panel.image = imgtk
               panel.grid(row = 0, column = 0)
               panel.bind('<Button-1>', self.dbg_img_mouse_callback)

               panel = tk.Label(frame, text = key)
               panel.grid(row = 1, column = 0, sticky = "nswe")

               ncol = ncol + 1
               if ncol > 1:
                  nrow = nrow + 1
                  ncol = 0

        # Add text information
        frame = tk.Frame(root)
        frame.grid(row = nrow, column = ncol, padx = 2, pady = 2, sticky = "nswe")

        lbox = tk.Listbox(frame)
        lbox.grid(row = 0, column = 0, sticky = "nswe")
        lbox.config(width = int(sx / 8))

        edges = res[GR_EDGES]
        spacing = res[GR_SPACING]
        hcross = res[GR_NUM_CROSS_H]
        vcross = res[GR_NUM_CROSS_W]
        size = res[GR_BOARD_SIZE]

        lbox.insert(tk.END, "Edges: ({},{}) : ({},{})".format(edges[0][0], edges[0][1], edges[1][0], edges[1][1]))
        lbox.insert(tk.END, "Net: {},{}".format(round(spacing[0],2), round(spacing[1],2)))
        lbox.insert(tk.END, "Cross: {},{}".format(hcross, vcross))
        lbox.insert(tk.END, "Size: {}".format(size))

        panel = tk.Label(frame, text = "TEXT_INFO")
        panel.grid(row = 1, column = 0, sticky = "nswe")

      # Update board
      def update_board(self, reprocess = True):
        # Process original image
        if self.grRes is None or reprocess:
           self.grRes = process_img(self.origImg, self.grParams)

        # Generate board using analysis results
        r = self.grRes.copy()
        if not self.showBlack:
           del r[GR_STONES_B]
        if not self.showWhite:
           del r[GR_STONES_W]

        self.genImg = generate_board(shape = self.origImg.shape, res = r)
        if self.showBoxes:
           if self.showBlack: self.show_detections(self.genImg, r[GR_STONES_B])
           if self.showWhite: self.show_detections(self.genImg, r[GR_STONES_W])

        self.genImgTk, _ = self.make_imgtk(self.genImg)
        self.genImgPanel.configure(image = self.genImgTk)

        board_size = self.grRes[GR_BOARD_SIZE]
        black_stones = self.grRes[GR_STONES_B]
        white_stones = self.grRes[GR_STONES_W]

        self.boardInfo.set("Board size: {}, black stones: {}, white stones: {}".format(
                                  board_size, black_stones.shape[0], white_stones.shape[0]))

        # Update debug info
        self.add_debug_info(self.dbgFrame, self.origImg.shape, self.grRes)

      # Convert origImg to ImageTk
      # If image size greater than maximim one, resize it to proper level and store zoom factor
      def make_imgtk(self, img):
          z = [1.0, 1.0]
          w = img.shape[CV_WIDTH]
          h = img.shape[CV_HEIGTH]
          if (w > self.MAX_IMG_SIZE and h > self.MAX_IMG_SIZE):
             if w >= h:
                z[GR_X] = float(self.MAX_IMG_SIZE) / float(w)
                z[GR_Y] = z[GR_X]
             else:
                z[GR_Y] = float(self.MAX_IMG_SIZE) / float(h)
                z[GR_X] = z[GR_Y]
          elif (w > self.MAX_IMG_SIZE):
             z[GR_X] = float(self.MAX_IMG_SIZE) / float(w)
             z[GR_Y] = z[GR_X]
          elif (h > self.MAX_IMG_SIZE):
             z[GR_Y] = float(self.MAX_IMG_SIZE) / float(h)
             z[GR_X] = z[GR_Y]

          img2 = cv2.resize(img, None, fx = z[GR_X],
                                       fy = z[GR_Y])
          imgtk = img_to_imgtk(img2)

          return imgtk, z

      # Display detections on board
      def show_detections(self, img, stones):
          for st in stones:
              x = st[GR_X]
              y = st[GR_Y]
              r = st[GR_R]
              cv2.circle(img, (x,y), r, (0,0,255), 1)

# Main function
def main():
    # Construct interface
    window = tk.Tk()
    window.title("Go board")
    gui = GbrGUI(window)

    # Main loop
    window.mainloop()

    # Clean up
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
