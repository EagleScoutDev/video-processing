import io
import os
import threading

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from tkVideoPlayer import TkinterVideo
from CTkMessagebox import CTkMessagebox

from ffmpeg import FFmpeg
from ffprobe import FFProbe
from yt_dlp import YoutubeDL
from PIL import Image, ImageTk

class LoadVideoFrame(ctk.CTkFrame):
    def __init__(self, master, file_path, next_button_enabled):
        super().__init__(master)
        self.file_path = file_path
        self.next_button_enabled = next_button_enabled

        self.label = ctk.CTkLabel(self, text="Load a video")
        self.label.pack(pady=20, padx=20)

        self.button = ctk.CTkButton(self, text="Select a video file", command=self.select_video)
        self.button.pack(pady=20, padx=20)

        ctk.CTkLabel(self, text="OR").pack(pady=20, padx=20)

        self.youtube_link = tk.StringVar(self, "")
        ctk.CTkLabel(self, text="Youtube video link:").pack(pady=20, padx=20)
        self.youtube_link_label = ctk.CTkEntry(self, textvariable=self.youtube_link)
        self.youtube_link_label.pack(pady=20, padx=20)

        self.youtube_button = ctk.CTkButton(self, text="Download", command=self.download_youtube_video)
        self.youtube_button.pack(pady=20, padx=20)

        self.file_path_label = ctk.CTkLabel(self, textvariable=self.file_path)
        self.file_path_label.pack(pady=20, padx=20)

    def select_video(self):
        filetypes = [("Video files", "*.mp4 *.mkv *.webm")]
        file_path = ctk.filedialog.askopenfile(filetypes=filetypes)
        if file_path:
            self.file_path.set(file_path.name)
            self.next_button_enabled.set(True)
    
    def download_youtube_video(self):
        thread = threading.Thread(target=self.download_youtube_video_target)
        thread.start()
        self.loading_label = ctk.CTkLabel(self, text="Downloading...")
        self.loading_label.pack(pady=20, padx=20)
    
    def download_youtube_video_target(self):
        ytdl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "outtmpl": "%(title)s.%(ext)s"
        }
        with YoutubeDL(ytdl_opts) as ytdl:
            info = ytdl.extract_info(self.youtube_link.get(), download=False)
            if info["extractor"] == "youtube":
                ytdl.download([self.youtube_link.get()])
                print(info)
                self.file_path.set(f"{info['title']}.{info['ext']}")
                self.next_button_enabled.set(True)
                self.loading_label.pack_forget()
            else:
                CTkMessagebox(title="Error", message="Invalid link", icon="cancel")


class TrimVideoFrame(ctk.CTkFrame):
    def __init__(self, master, file_path, start_time, end_time, next_button_enabled):
        super().__init__(master)
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.next_button_enabled = next_button_enabled

        self.label = ctk.CTkLabel(self, text="Trim the video")
        self.label.pack(pady=20, padx=20)

        self.video_player = TkinterVideo(self, scaled=True, keep_aspect=True)
        self.video_player.pack(fill="both", expand=True)
        file_path.trace_add("write", lambda *args: self.load_video())
        self.video_player.bind("<<Duration>>", self.update_duration)
        self.video_player.bind("<<SecondChanged>>", self.update_scale)

        self.curr_timestamp = tk.IntVar(self, 0)

        self.scrub_slider = ttk.Scale(self, variable=self.curr_timestamp, from_=0, to=0, orient="horizontal", command=self.seek_video)
        self.scrub_slider.pack(pady=20, padx=20, fill="x")
        self.scrub_slider.bind("<ButtonRelease-1>", lambda evt: self.video_player.seek(int(float(self.curr_timestamp.get()))))

        self.play_button = ctk.CTkButton(self, text="Play", command=self.toggle_video_state)
        self.play_button.pack(pady=20, padx=20)

        self.start_frame = ctk.CTkFrame(self)
        ctk.CTkButton(self.start_frame, text="Set as start time", command=lambda: self.start_time.set(self.curr_timestamp.get())).pack(side="left")
        self.start_time_label_text = tk.StringVar(self, "Start time: 00:00:00")
        self.start_time_label = ctk.CTkLabel(self.start_frame, textvariable=self.start_time_label_text)
        self.start_time_label.pack(side="left")
        self.start_frame.pack(pady=20, padx=20)

        self.end_frame = ctk.CTkFrame(self)
        ctk.CTkButton(self.end_frame, text="Set as end time", command=lambda: self.end_time.set(self.curr_timestamp.get())).pack(side="left")
        self.end_time_label_text = tk.StringVar(self, "End time: 00:00:00")
        self.end_time_label = ctk.CTkLabel(self.end_frame, textvariable=self.end_time_label_text)
        self.end_time_label.pack(side="left")
        self.end_frame.pack(pady=20, padx=20)

        self.start_time.trace_add("write", lambda *args: self.render_time())
        self.end_time.trace_add("write", lambda *args: self.render_time())

    def update_duration(self, event):
        duration = self.video_player.video_info()["duration"]
        self.scrub_slider["to"] = duration
    
    def update_scale(self, event):
        self.curr_timestamp.set(self.video_player.current_duration())

    def seek_video(self, value):
        self.video_player.seek(int(float(value)))
    
    def render_time(self):
        start_time = self.start_time.get()
        end_time = self.end_time.get()
        self.start_time_label_text.set(f"Start time: {start_time // 3600:02}:{(start_time // 60) % 60:02}:{start_time % 60:02}")
        self.end_time_label_text.set(f"End time: {end_time // 3600:02}:{(end_time // 60) % 60:02}:{end_time % 60:02}")
        if start_time and end_time:
            self.next_button_enabled.set(True)
    
    def load_video(self):
        self.video_player.load(self.file_path.get())
    
    def toggle_video_state(self):
        if self.video_player.is_paused():
            self.video_player.play()
            self.play_button.configure(text="Pause")
        else:
            self.video_player.pause()
            self.play_button.configure(text="Play")

class CropVideoFrame(ctk.CTkFrame):
    def __init__(self, master, file_path, start_time, end_time, top_x, top_y, bottom_x, bottom_y, coords_scale, next_button_enabled):
        super().__init__(master)
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.top_x = top_x
        self.top_y = top_y
        self.bottom_x = bottom_x
        self.bottom_y = bottom_y
        self.coords_scale = coords_scale
        self.next_button_enabled = next_button_enabled

        self.label = ctk.CTkLabel(self, text="Select crop area")
        self.label.pack(padx=20)

        outer_frame = ctk.CTkFrame(self)
        self.generate_label(outer_frame, "Top X:", self.top_x)
        self.generate_label(outer_frame, "Top Y:", self.top_y)
        self.generate_label(outer_frame, "Bottom X:", self.bottom_x)
        self.generate_label(outer_frame, "Bottom Y:", self.bottom_y)
        # put to the right of the screen
        outer_frame.pack(pady=20, padx=20, side="right")

        self.start_time.trace_add("write", lambda *args: self.intialize_canvas())

    def generate_label(self, outer_frame, text, variable):
        frame = ctk.CTkFrame(outer_frame)
        text_str = tk.StringVar(self, f"{text}: {variable.get() * self.coords_scale.get()}")
        ctk.CTkLabel(frame, textvariable=text_str).pack(side="left")
        variable.trace_add("write", lambda *args: text_str.set(f"{text}: {variable.get() * self.coords_scale.get()}"))
        frame.pack(pady=20, padx=20)

    def intialize_canvas(self):
        if hasattr(self, "canvas"):
            self.canvas.pack_forget()
        if self.file_path.get() == "":
            return
        self.ffmpeg_output = FFmpeg()\
            .input(self.file_path.get(), ss=self.start_time.get())\
            .output("pipe:1", vframes=1, f="image2", vcodec="png")\
            .execute()

        self.image = Image.open(io.BytesIO(self.ffmpeg_output))
        # set width to 1024 and height to maintain aspect ratio
        WIDTH = int(0.7 * 1280)
        w = WIDTH
        h = WIDTH * self.image.height // self.image.width
        if h > WIDTH:
            h = WIDTH
            w = WIDTH * self.image.width // self.image.height
        self.coords_scale.set(self.image.width / w)
        self.canvas = ctk.CTkCanvas(self, width=w, height=h)
        # resize the image to fit the canvas
        self.image = ImageTk.PhotoImage(self.image.resize((w, h)))
        self.canvas.create_image(0, 0, image=self.image, anchor="nw")
        self.canvas.pack(pady=20, padx=20)

        # handle mouse click events
        self.canvas.bind("<Button-1>", self.on_click)
    
    def on_click(self, event):
        if hasattr(self, "rect"):
            self.canvas.delete(self.rect_id)
        self.rect = [event.x, event.y, event.x, event.y]
        self.rect_id = self.canvas.create_rectangle(self.rect, outline="red", width=2)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
    def on_drag(self, event):
        self.rect[2], self.rect[3] = event.x, event.y
        self.canvas.coords(self.rect_id, self.rect)

    def on_release(self, event):
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.top_x.set(self.rect[0])
        self.top_y.set(self.rect[1])
        self.bottom_x.set(self.rect[2])
        self.bottom_y.set(self.rect[3])
        self.next_button_enabled.set(True)

class ExportVideoFrame(ctk.CTkFrame):
    def __init__(self, master, file_path, start_time, end_time, top_x, top_y, bottom_x, bottom_y, coords_scale):
        super().__init__(master)
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        self.top_x = top_x
        self.top_y = top_y
        self.bottom_x = bottom_x
        self.bottom_y = bottom_y
        self.coords_scale = coords_scale

        self.label = ctk.CTkLabel(self, text="Export the video")
        self.label.pack(pady=20, padx=20)

        self.export_button = ctk.CTkButton(self, text="Export", command=self.export_video)
        self.export_button.pack(pady=20, padx=20)

    def export_video(self):
        save_as = ctk.filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("Video files", "*.mp4")])
        if not save_as:
            return
        probe_res = FFProbe(self.file_path.get()).streams[0]
        fps = probe_res.framerate
        total_frames = (self.end_time.get() - self.start_time.get()) * fps
        print("Exporting video"
            f"\nFile path: {self.file_path.get()}"
            f"\nSave as: {save_as}"
            f"\nTotal frames: {total_frames}"
            f"\nStart time: {self.start_time.get()}"
            f"\nEnd time: {self.end_time.get()}"
            f"\nTop left: ({self.top_x.get() * self.coords_scale.get()}, {self.top_y.get() * self.coords_scale.get()})"
            f"\nBottom right: ({self.bottom_x.get() * self.coords_scale.get()}, {self.bottom_y.get() * self.coords_scale.get()})")

        self.bar = ctk.CTkProgressBar(self)
        self.bar.pack(pady=20, padx=20, fill="x")
        res = FFmpeg()\
            .input(self.file_path.get(), ss=self.start_time.get(), to=self.end_time.get())\
            .output(save_as, vf=f"crop={self.coords_scale.get() * (self.bottom_x.get() - self.top_x.get())}:{self.coords_scale.get() * (self.bottom_y.get() - self.top_y.get())}:{self.coords_scale.get() * self.top_x.get()}:{self.coords_scale.get() * self.top_y.get()}", vcodec="libx264")\

        @res.on("progress")
        def on_progress(progress):
            # print(progress)
            self.bar.set(progress.frame / total_frames)
        
        @res.on("completed")
        def on_completed():
            self.bar.pack_forget()
            print("Video exported")
            os.remove(self.file_path.get())
            CTkMessagebox(title="Success", message="Video exported", icon="info")
        
        thread = threading.Thread(target=res.execute)
        thread.start()
        

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1280x720")
        self.resizable(False, False)
        self.title("Video Processor")

        self.ttk_style = ttk.Style()
        self.ttk_style.layout("TNotebook.Tab", [])

        '''
        0: Load a video
        1: Trim the video
        2: Select crop area
        3: Export the video
        '''
        self.current_step = tk.IntVar(self, 0)
        self.current_step.trace_add("write", lambda *args: self.update_progress())
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=20, padx=20, fill="x")

        self.next_button_enabled = tk.BooleanVar(self, False)
        self.file_path = tk.StringVar(self, "")
        self.start_time = tk.IntVar(self, 0)
        self.end_time = tk.IntVar(self, 0)
        self.top_x = tk.IntVar(self, 0)
        self.top_y = tk.IntVar(self, 0)
        self.bottom_x = tk.IntVar(self, 0)
        self.bottom_y = tk.IntVar(self, 0)
        self.coords_scale = tk.DoubleVar(self, 0)

        self.next_button = ctk.CTkButton(self, text="Next", command=self.next_step, state="disabled")
        self.next_button.pack(side="bottom", padx=20, pady=20)
        self.next_button_enabled.trace_add("write", lambda *args: self.next_button.configure(state="normal") if self.next_button_enabled.get() else self.next_button.configure(state="disabled"))

        self.load_video_frame = LoadVideoFrame(self, self.file_path, self.next_button_enabled)
        self.trim_video_frame = TrimVideoFrame(self, self.file_path, self.start_time, self.end_time, self.next_button_enabled)
        self.crop_video_frame = CropVideoFrame(self, self.file_path, self.start_time, self.end_time, self.top_x, self.top_y, self.bottom_x, self.bottom_y, self.coords_scale, self.next_button_enabled)
        self.export_video_frame = ExportVideoFrame(self, self.file_path, self.start_time, self.end_time, self.top_x, self.top_y, self.bottom_x, self.bottom_y, self.coords_scale)

        self.update_progress()
    
    def update_progress(self):
        self.progress_bar.set(self.current_step.get() * 1/3)
        self.load_video_frame.pack_forget()
        self.trim_video_frame.pack_forget()
        self.crop_video_frame.pack_forget()
        self.export_video_frame.pack_forget()
        if self.current_step.get() == 0:
            self.load_video_frame.pack(fill="both", expand=True)
        elif self.current_step.get() == 1:
            self.trim_video_frame.pack(fill="both", expand=True)
        elif self.current_step.get() == 2:
            self.crop_video_frame.pack(fill="both", expand=True)
        elif self.current_step.get() == 3:
            self.export_video_frame.pack(fill="both", expand=True)
    
    def next_step(self):
        if self.current_step.get() == 2:
            self.next_button.configure(text="Reset")
            self.current_step.set(self.current_step.get() + 1)
            return
        if self.current_step.get() == 3:
            self.current_step.set(0)
            self.file_path.set("")
            self.start_time.set(0)
            self.end_time.set(0)
            self.top_x.set(0)
            self.top_y.set(0)
            self.bottom_x.set(0)
            self.bottom_y.set(0)
            self.coords_scale.set(0)
            self.next_button_enabled.set(False)
            self.next_button.configure(text="Next")
            return
        self.current_step.set(self.current_step.get() + 1)
        self.next_button_enabled.set(False)

app = App()
app.mainloop()