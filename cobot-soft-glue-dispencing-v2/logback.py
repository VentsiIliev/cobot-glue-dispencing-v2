from PIL import Image

# Input/output paths
input_path = r"/home/plp/cobot-soft-v2/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/pl_gui/resources/pl_ui_icons/Background_&_Logo.png"
output_path = r"/home/plp/cobot-soft-v2/cobot-glue-dispencing-v2/cobot-soft-glue-dispencing-v2/pl_gui/resources/pl_ui_icons/Background_&_Logo_white.png"

# Open image
img = Image.open(input_path).convert("RGBA")
datas = img.getdata()

new_data = []
for item in datas:
    r, g, b, a = item
    # Detect black (or almost black) background
    if r < 20 and g < 20 and b < 20:
        new_data.append((255, 255, 255, 255))  # Replace with white
    else:
        new_data.append((r, g, b, a))

img.putdata(new_data)

# Convert to RGB and save
img = img.convert("RGB")
img.save(output_path)

print(f"Image saved at {output_path}")
