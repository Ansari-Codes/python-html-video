import os
from pathlib import Path
from time import sleep
from progressive_py.progress_bar import ProgressBar
import warnings
warnings.filterwarnings("ignore")

from llms import (
    generate_scenes,
    generate_approach,
    generate_animations,
    generate_audio,
    generate_storyboard,
    generate_raw_html,
    generate_styles,
    generate_transcript,
)
from storage import (
    STAGES,
    create_scene,
    load_assets,
    format_assets,
    load_scene_meta,
    load_status,
    initialize_project,
    load_project_meta,
    save_approach,
    load_approach,
    save_audio,
    load_storyboard,
    save_storyboard,
    save_html,
    save_transcript,
)

project_user = input("Project: ")
folder = Path().cwd()/ "Projects" / project_user

if not folder.exists(): 
    os.makedirs(folder)
    prompt = input("Prompt: ")
    scenes = generate_scenes(prompt)
    project = initialize_project(folder, project_user, prompt, scenes)
    project['scenes'] = scenes
else:
    project = load_project_meta(folder)
    scenes = project["scenes"]

assets = load_assets(folder)
formatted_assets = format_assets(assets)
created_scenes = []

for idx, s in enumerate(scenes):
    if s['status']: continue
    s_no = idx + 1
    meta, status = create_scene(folder, s_no, s['title'], s['duration'])
    created_scenes.append([meta, status])

for scene in created_scenes:
    total_stages = 6

    meta = scene[0]
    status = scene[1]
    s_no = meta['number']

    pbar = ProgressBar({
            'txt_lf': f'Scene #{s_no} [{{percent}}%] [Stage: {{stage}}] |',
            'txt_rt': '| Elapsed: {elapsed}',
            'tokens': {'stage': lambda p: [
                'Generating Approach...', 
                'Generating Transcript...',
                'Creating Storyboard...', 
                'Generating Html blockout...',
                'Styling Html...', 
                'Animating Html...'
            ][p.current_iter if 6 >= p.current_iter >= 0 else 0]}
        })
    
    previous_scenes = []
    previous_approaches = []
    previous_storyboards = []
    next_scenes = []
    
    if s_no > 1:
        previous_scenes = [load_scene_meta(folder, i) for i in range(1, s_no)]
        previous_approaches = [load_approach(folder, i) for i in range(1, s_no)]
        previous_storyboards = [load_storyboard(folder, i) for i in range(1, s_no)]
        
        previous_approaches.reverse()
        previous_storyboards.reverse()
        
    if s_no < len(scenes):
        next_scenes = [load_scene_meta(folder, i) for i in range(s_no + 1, len(scenes) + 1)]

    approach = generate_approach(
            meta,
            [p['title'] for p in previous_scenes] if previous_scenes else [],
            [p['title'] for p in next_scenes] if next_scenes else [],
            previous_approaches[0:3] if previous_approaches else [],
            previous_storyboards[0:3] if previous_storyboards else [],
            formatted_assets,
        )

    save_approach(folder, s_no, approach)
    status[STAGES.approach] = True
    sleep(20)
    pbar.update(1/total_stages, 1, total_stages)

    transcript = generate_transcript(meta, approach)
    save_transcript(folder, s_no, transcript)
    status[STAGES.transcription] = True
    sleep(20)
    pbar.update(2/total_stages, 2, total_stages)

    storyboard = generate_storyboard(meta, approach, transcript, formatted_assets, previous_storyboards[0] if previous_storyboards else "")
    save_storyboard(folder, s_no, storyboard)
    status[STAGES.storyboard] = True
    sleep(20)
    pbar.update(3/total_stages, 3, total_stages)

    raw_html = generate_raw_html(meta, storyboard, formatted_assets)
    save_html(folder, s_no, raw_html)
    status[STAGES.html] = True
    sleep(20)
    pbar.update(4/total_stages, 4, total_stages)

    stylized_html = generate_styles(meta, storyboard, raw_html)
    save_html(folder, s_no, stylized_html)
    status[STAGES.styling] = True
    sleep(20)
    pbar.update(5/total_stages, 5, total_stages)

    animated_html = generate_animations(meta, storyboard, stylized_html)
    save_html(folder, s_no, animated_html)
    status[STAGES.animation] = True
    sleep(20)
    pbar.update(6/total_stages, 6, total_stages)
    pbar.update(1, total_stages, total_stages)
    
    