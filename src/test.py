# -*- coding: utf-8 -*-

from moviepy.editor import *
import csv
import sys
from datetime import datetime
icon_manager = 'icon_manager is not initialized'



"""
Main function
"""
def main(data_path, footage_path):
    skip_rows = 90
    video_seconds = 15
    data = parse_logs(data_path, skip_rows)
    footage_clip_res = (720, 1280)
    info_clip_res = (720, 1280) # half of the video
    info_line_res = (720, 256) # 5 lines
    icon_res = (256, 256) # biggest square possible

    print 'Creating icon manager...'
    global icon_manager
    icon_manager = IconManager(resolution=icon_res)

    print 'Generating Footage Clip...'
    footage_clip = generate_footage_clip(footage_path, footage_clip_res, video_seconds)

    print 'Generating Info Clip...'
    info_clip = generate_info_clip(data, info_clip_res, video_seconds)

    print 'Compositing footage and info clips...'
    clip = clips_array([[footage_clip, info_clip.set_pos('center')]])

    print 'Rendering...'
    #clip.write_videofile("onewheel.MP4", fps=60)
    #clip.resize(0.5).preview(fps=60, audio=False)
    info_clip.resize(0.5).preview(fps=60, audio=False)

"""
Opens and loads the video clip captured by the Go Pro
"""
def generate_footage_clip(file_path, resolution, clip_length):
    return (VideoFileClip(file_path)
            .subclip(t_end=clip_length)
            .rotate(-90)
            .resize(resolution))

"""
Generates the clip that will show the data gathered by the App
"""
def generate_info_clip(data, resolution, clip_length):
    n_info_lines = 5
    info_line_resolution = (resolution[0], resolution[1]/n_info_lines)
    print "Generating {} info lines with resolution {}".format(n_info_lines, info_line_resolution)

    speed_text = generate_info_line_clip(data, info_line_resolution, clip_length, '{:>5.1f} Km/h', 'speed', '../data/speed.png')
    battery_text = generate_info_line_clip(data, info_line_resolution, clip_length, '{:>3d}%', 'battery', '../data/battery.png')
    roll_text = generate_info_line_clip(data, info_line_resolution, clip_length, '{:>5.1f}°', 'roll', '../data/roll.png')
    pitch_text = generate_info_line_clip(data, info_line_resolution, clip_length, '{:>5.1f}°', 'pitch', '../data/pitch.png')
    temp_text = generate_info_line_clip(data, info_line_resolution, clip_length, '{:>5.1f} C', 'motor_temp', '../data/temp.png')

    print 'Compositing lines together...'
    info_text_clip = clips_array([
        [speed_text],
        [pitch_text],
        [roll_text],
        [battery_text],
        [temp_text]
    ])

    bg_clip = TextClip(' ', size=resolution, bg_color='white').set_duration(clip_length)
    info_text_clip = CompositeVideoClip([bg_clip, info_text_clip])

    return info_text_clip

def generate_info_line_clip(data,  resolution, clip_length, text, column_name, icon_path):
    print 'Generating {} info line clip. {}'.format(column_name, resolution)
    info_clips = []
    global icon_manager
    icon_resolution=(resolution[1], resolution[1])
    for i in range(clip_length):
        data_str = data[i][column_name]
        icon_clip = {
            'pitch': icon_manager.get_pitch_icon_clip(angle=float(data_str)),
            'roll': icon_manager.get_roll_icon_clip(angle=float(data_str)),
            'speed': icon_manager.get_speed_icon_clip(),
            'battery': icon_manager.get_battery_icon_clip(),
            'motor_temp': icon_manager.get_temperature_icon_clip()
        }[column_name]

        txt_resolution = (resolution[0] - icon_resolution[0], resolution[1])
        txt_clip = generate_info_text_clip(text.format(data_str), txt_resolution, 1, 100)

        txt_icon_clip = clips_array([[icon_clip, txt_clip.set_pos("center")]])
        info_clips.append(txt_icon_clip)

    line_clip = concatenate_videoclips(info_clips)
    return line_clip

def generate_info_text_clip(text, resolution, clip_length, padding):
    txt_clip = (TextClip(text, fontsize=70, color='blue', font='Consolas')
                .set_duration(clip_length)
                .on_color(col_opacity=0, size=resolution, pos=('left', 'center')))
    return txt_clip

"""
Converts Miles to Kilometers
"""
def mile2Km(mile):
    return float(mile) * 1.609344

"""
Converts from Farenheint to Celsius
"""
def f_to_c(f_temp):
    try:
        return (float(f_temp) - 32) * 5.0 / 9.0
    except ValueError:
        return None

"""
Converts the original angle to values between -180 and 180, with 0 being horizontal
"""
def parse_angle(angle_text):
    try:
        return float(angle_text)/10 - 180
    except ValueError:
        return None

"""
Parses the log files and creates a list of dicts
"""
def parse_logs(file_path, skip_rows=0):
    print 'Loading log file ', file_path, '...'
    data = []
    with open(file_path) as logfile:
        log_reader = csv.DictReader(logfile)
        for row in log_reader:
            data.append({
                'time':parse_milisecond_time(row['time']),
                'speed':mile2Km(row['speed']),
                'battery':int(row['battery']),
                'roll':parse_angle(row['tilt_angle_roll']),
                'pitch':parse_angle(row['tilt_angle_pitch']),
                'motor_temp':f_to_c(row['motor_temp'])
                })
    print 'Loaded ', len(data), 'rows'
    return data[skip_rows:]

def parse_original_time(time_str):
    # remove timezone info
    time_str = time_str[:-5]
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')

def parse_milisecond_time(time_str): # "yyyy-MM-dd'T'HH:mm:ss.SSSZ"
    # remove timezone info
    time_str = time_str[:-5]
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')

def test_data(data):
    deltas=[]
    for i, row in enumerate(data):
        if i+1 < len(data):
            delta_t = data[i+1]['time'] - row['time']
            delta_seconds = delta_t.seconds + delta_t.microseconds * 1e-6
            deltas.append(delta_seconds)
    print len(deltas)
    print max(deltas)
    print min(deltas)
    print sum(deltas)/len(deltas)
    print sorted(deltas)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Wrong number of arguments.'
        print 'Usage: python test.py <data_path> <footage_path>'
        exit(1)

    from OnewheelHudVideo import OnewheelHudVideo
    onewheel_video = OnewheelHudVideo(sys.argv[1], sys.argv[2])
    onewheel_video.render()
    #test_data(parse_logs(sys.argv[1]))
