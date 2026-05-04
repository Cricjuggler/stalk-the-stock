Drop your source images here (the ones with backgrounds), then run:

    python tools/prepare_avatars.py

from the formcheck/ directory. The script removes the background and saves the
results into ../frontend/assets/ with the correct names automatically.

EXPECTED FILENAMES (any extension works: .png .jpg .jpeg .webp):

    headshot.*          black background, head/torso shot      -> stalky.png
    full.*              white/transparent bg, full body        -> stalky-full.png
    pose-thinking.*     white bg                                -> stalky-thinking.png
    pose-excited.*      white bg                                -> stalky-excited.png
    pose-sad.*          white bg                                -> stalky-sad.png
    pose-wink.*         white bg                                -> stalky-wink.png

You only need the files you actually want — missing ones are skipped silently.

If you have one big pose-sheet image with all 10 poses, crop them out manually
into individual PNGs first (any image editor: Photopea.com works in the browser).
