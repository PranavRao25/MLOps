# logging conflicts

#### 1st conflict:
- the conflict was in requirements.txt, we made 2 files with different requirements for each person's features
- resolution: we accepted changes from both the sources and then refactored the file 

#### 2nd conflict:
- Pranav committed the NER feature, while Sanved was working on the blank  template at the beginning
- Both devs worked separately on the features. Sanved's branch `translate` was left behind the new `main` once pranav's PR was accepted.
- config.yaml had a conflict
- resolution: we fixed the src directory, made a common app.py, fixed the conflict in config.yaml

#### 3rd conflict: 
- Sanved worked on and pushed the translate feature. 
- Then Pranav worked on the `tts` branch for a new feature. Made a PR for it. There were no conflicts. 
- Then Sanved pushed the new `test_app.py`, no conflicts there. 
- Once both were done, Sanved updated the `image_generation` branch once more, added more files. He had the previous versions for `requirements.txt` and `config.yaml` that Pranav had updated. 
- Conflicts were there for both files. 
- resolution: we accepted changes from both sources, fixed inconsistencies.  