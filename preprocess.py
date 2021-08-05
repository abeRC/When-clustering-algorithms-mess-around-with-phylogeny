import os

ORIG_FOLDER = "family_pages"
MOD_FOLDER = "family_pages_mod"

def preprocess (file):
    filepath = os.path.join(ORIG_FOLDER, file)
    with open(filepath, "r") as f:
        lines = f.readlines()
    
    mod = []
    for l in lines:
        if not l or len(l.strip()) == 0:
            continue
        if "== References ==" in l: # stopping point (I'll choose to keep 'See Also', though.)
            break
        elif "==" in l: # ignore section names
            continue

        mod.append(l.casefold())
    
    newpath = os.path.join(MOD_FOLDER, file)
    with open(newpath, "w") as f:
        f.write("\n".join(mod))

def main ():
    os.makedirs(MOD_FOLDER, exist_ok=True)

    for file in os.listdir(ORIG_FOLDER):
        if file.endswith(".txt"): # just in case, you know!
            preprocess(file)

if __name__ == "__main__":
    main()