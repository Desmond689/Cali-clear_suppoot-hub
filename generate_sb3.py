import json
import zipfile
import os

def create_sb3():
    # Define the project.json structure for a more advanced Windows-like Scratch project
    project_data = {
        "targets": [
            {
                "isStage": True,
                "name": "Stage",
                "variables": {
                    "window_count": ["window_count", 0]
                },
                "lists": {},
                "broadcasts": {},
                "blocks": {},
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "Windows Desktop",
                        "dataFormat": "svg",
                        "assetId": "cd21514d0531fdffb22204e0ec5ed84a",
                        "md5ext": "cd21514d0531fdffb22204e0ec5ed84a.svg",
                        "rotationCenterX": 240,
                        "rotationCenterY": 180
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 0,
                "tempo": 60,
                "videoTransparency": 50,
                "videoState": "on",
                "textToSpeechLanguage": None
            },
            {
                "isStage": False,
                "name": "Start Menu",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "block1": {
                        "opcode": "event_whenflagclicked",
                        "next": "block2",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 100,
                        "y": 100
                    },
                    "block2": {
                        "opcode": "looks_say",
                        "next": "block3",
                        "parent": "block1",
                        "inputs": {
                            "MESSAGE": [1, [10, "Welcome to Windows!"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block3": {
                        "opcode": "control_wait",
                        "next": "block4",
                        "parent": "block2",
                        "inputs": {
                            "DURATION": [1, [4, "2"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block4": {
                        "opcode": "looks_say",
                        "next": None,
                        "parent": "block3",
                        "inputs": {
                            "MESSAGE": [1, [10, "Click me to open a window!"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block5": {
                        "opcode": "event_whenclicked",
                        "next": "block6",
                        "parent": None,
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 200,
                        "y": 100
                    },
                    "block6": {
                        "opcode": "event_broadcast",
                        "next": None,
                        "parent": "block5",
                        "inputs": {
                            "BROADCAST_INPUT": [1, [11, "open_window", "open_window"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    }
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "Start Button",
                        "dataFormat": "svg",
                        "assetId": "83a9787d4cb6f3b7632b4ddfebf74367",
                        "md5ext": "83a9787d4cb6f3b7632b4ddfebf74367.svg",
                        "rotationCenterX": 50,
                        "rotationCenterY": 50
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 1,
                "visible": True,
                "x": -200,
                "y": -150,
                "size": 100,
                "direction": 90,
                "draggable": False,
                "rotationStyle": "all around"
            },
            {
                "isStage": False,
                "name": "Window",
                "variables": {},
                "lists": {},
                "broadcasts": {},
                "blocks": {
                    "block7": {
                        "opcode": "event_whenbroadcastreceived",
                        "next": "block8",
                        "parent": None,
                        "inputs": {
                            "BROADCAST_OPTION": [1, [11, "open_window", "open_window"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": True,
                        "x": 300,
                        "y": 100
                    },
                    "block8": {
                        "opcode": "looks_show",
                        "next": "block9",
                        "parent": "block7",
                        "inputs": {},
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block9": {
                        "opcode": "motion_gotoxy",
                        "next": "block10",
                        "parent": "block8",
                        "inputs": {
                            "X": [1, [4, "0"]],
                            "Y": [1, [4, "0"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    },
                    "block10": {
                        "opcode": "looks_say",
                        "next": None,
                        "parent": "block9",
                        "inputs": {
                            "MESSAGE": [1, [10, "This is a window!"]]
                        },
                        "fields": {},
                        "shadow": False,
                        "topLevel": False
                    }
                },
                "comments": {},
                "currentCostume": 0,
                "costumes": [
                    {
                        "name": "Window",
                        "dataFormat": "svg",
                        "assetId": "5c81a336fab8be57adc039a8a2b33ca9",
                        "md5ext": "5c81a336fab8be57adc039a8a2b33ca9.svg",
                        "rotationCenterX": 100,
                        "rotationCenterY": 75
                    }
                ],
                "sounds": [],
                "volume": 100,
                "layerOrder": 2,
                "visible": False,
                "x": 0,
                "y": 0,
                "size": 100,
                "direction": 90,
                "draggable": True,
                "rotationStyle": "don't rotate"
            }
        ],
        "monitors": [],
        "extensions": [],
        "meta": {
            "semver": "3.0.0",
            "vm": "0.2.0",
            "agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    }

    # Write project.json
    with open('project.json', 'w') as f:
        json.dump(project_data, f, indent=2)

    # Create the .sb3 zip file
    with zipfile.ZipFile('windows_desktop.sb3', 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write('project.json')

    # Clean up
    os.remove('project.json')

    print("Sb3 file 'windows_desktop.sb3' created successfully!")
    print("This project simulates a basic Windows desktop with a start menu and window opening functionality.")

if __name__ == "__main__":
    create_sb3()
