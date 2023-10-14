from flask import Flask, request, jsonify
from flask_cors import CORS
import pywhatkit as kit
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import base64

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('config.py')

@app.route('/send_image', methods=['POST'])
def send_image():
    recipient_phone_number = f'+91 {request.form.get("recipient_phone_number")}'
    image_file = request.form.get('image_path')
    caption = request.form.get('caption')
    headerText = request.form.get('header')
    footerText = request.form.get('footer')
    if not recipient_phone_number or not image_file:
        return jsonify({'error': 'Recipient phone number and image path are required'}), 400
    
    try:
        new_size = (800, 600)  # Replace with your desired dimensions
        image = Image.open(image_file).resize(new_size)

        draw = ImageDraw.Draw(image)
        
        font_path = "./otf_files/Montserrat-Black.otf"
        header_footer_font_size = 30
        font = ImageFont.truetype(font_path, header_footer_font_size)

        header_text = headerText
        footer_text = footerText
        wrapped_header_text = textwrap.fill(header_text, width=40)
        wrapped_footer_text = textwrap.fill(footer_text, width=40)
        text_color = (255, 255, 255)  # RGB color code (white in this example)

        image_width, image_height = image.size
        header_text_width = draw.textlength(wrapped_header_text, font=font)
        footer_text_width = draw.textlength(wrapped_footer_text, font=font)

        header_text_x = (image_width - header_text_width) // 2

        footer_text_x = (image_width - footer_text_width) // 2


        header_text_y = 20
        footer_text_y = image_height - header_footer_font_size * 2


        draw.text((header_text_x, header_text_y), wrapped_header_text, fill=text_color, font=font)
        draw.text((footer_text_x, footer_text_y), wrapped_footer_text, fill=text_color, font=font)


        image.save("output_image.jpg")

        kit.sendwhats_image(recipient_phone_number, './output_image.jpg', caption, 15, False, 3)
        

        image.close()
        os.remove("output_image.jpg")
        
        return jsonify({'message': 'Image sent successfully'})
    except Exception as e:
        return jsonify({'message': 'Failed to send image'}), 500

@app.route('/load_image_gallery', methods=['GET'])
def load_image_gallery():
    try:
        # Get the folder path from the request
        folder_path = f'{app.config["ROOT_DIR"]}{request.args.get("folder_path", "")}'
        print(folder_path)
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 9))
        if not folder_path:
            return jsonify({'error': 'Please provide a folder path'}), 400
        start_idx = (page - 1) * per_page
        image_data_list = dict(get_blob_url_from_folder(folder_path, start_idx, per_page))
        return jsonify({'imageList': image_data_list.get('image_blob_urls'), 'count': image_data_list.get('file_count')})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def count_files_with_extensions(folder_path, extensions):
    try:
        if not os.path.exists(folder_path):
            return 0  # Return 0 if the folder doesn't exist

        file_count = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_count += 1

        return file_count
    except Exception as e:
        return 0  # Handle any errors gracefully
      
def get_blob_url_from_folder(folder_path, start_idx, per_page):
    # Scan the folder for image files (you can adjust the extensions as needed)
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    image_blob_urls = []
    file_count = count_files_with_extensions(folder_path,image_extensions)
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(root, file)
                if start_idx > 0:
                    start_idx -= 1
                else:
                    with open(image_path, 'rb') as image_file:
                        # Create a Blob from the binary image data
                        image_data = image_file.read()
                        image_blob_url = create_blob_url(image_data)
                        image_blob_urls.append({'path': image_path, 'url': image_blob_url, 'style': "none"})
                        # Break if we have collected 'per_page' images
                        if len(image_blob_urls) >= per_page:
                            break

        # Break if we have collected 'per_page' images
        if len(image_blob_urls) >= per_page:
            break

    return {'image_blob_urls': image_blob_urls,'file_count':file_count }    

def create_blob_url(binary_data):
    # In Python, you can use the base64 module to encode binary data as Base64
    base64_data = base64.b64encode(binary_data).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"

@app.route("/delete_image", methods=["DELETE"])
def delete_image():
    try:
        # Get the file path from the request body
        data = request.get_json()
        file_path = data.get('path')

        if not file_path:
            return jsonify({'error': 'Please provide a valid file path'}), 400

        # Check if the file exists
        if os.path.exists(file_path):
            # Delete the file
            os.remove(file_path)
            return jsonify({'message': 'File deleted successfully'}), 200
        else:
            return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Server is listening on port {app.config['PORT']}")
    app.run(debug=False, port=app.config['PORT'])
    

