import requests
import base64

IMGBB_API_KEY = "5a43c16114ccb592a47a790a058fcf65"

def upload_to_imgbb(file_path):
    url = "https://api.imgbb.com/1/upload"
    
    with open(file_path, 'rb') as file:
        image_data = base64.b64encode(file.read()).decode('utf-8')
        
        response = requests.post(
            url,
            data={
                'key': IMGBB_API_KEY,
                'image': image_data,  
            }
        )
    
    data = response.json()
    if response.status_code == 200 and data['success']:
        return data['data']['url']
    else:
        raise Exception(f"ImgBB upload failed: {data.get('error', 'Unknown error')}")