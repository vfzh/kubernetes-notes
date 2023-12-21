import os
import json
import time
import magic
import random
import re
import base64
from django.views.decorators.csrf import csrf_exempt


date = time.strftime('%Y%m%d')
UPLOAD_FILE_PATH = '/home/ap/safm/upload/'
isExists=os.path.exists(UPLOAD_FILE_PATH)
if not isExists:
    os.makedirs(UPLOAD_FILE_PATH)
else:
    print('path isexist!')


from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("Hello Django!")

def get_random_str(randomlength=16):
  random_str = ''
  base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
  length = len(base_str) - 1
  print(length)
  for i in range(randomlength):
    random_str += base_str[random.randint(0, length)]
  return random_str

@csrf_exempt
def download(request):
    request_params = request.GET
    print(request_params)


@csrf_exempt
def upload(request):
    allow = ['rar','zip','pdf','doc','docx','xls','xlsx','ppt','pptx','ppsx','jpg','png','gif','bmp','mp4','avi','wav','mp3','txt','jpeg','dwg','dxf','dwf','csv','mov']
    allow_type = ['application/x-rar-compressed','application/zip','application/pdf','application/msword','application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.ms-excel','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.ms-powerpoint','application/vnd.openxmlformats-officedocument.presentationml.presentation','application/vnd.openxmlformats-officedocument.presentationml.slideshow','image/jpeg','image/png','image/gif','image/bmp','video/mp4','video/x-msvideo','audio/x-wav','audio/mpeg','text/plain','image/jpeg','text/csv','video/quicktime','image/vnd.dwg','image/vnd.dxf','model/vnd.dwf']
    request_params = request.POST
    print(request_params)
    file_name = request_params['file_name']
    file_content_type = request_params['file_content_type']
    file_md5 = request_params['file_md5']
    file_path = request_params['file_path']
    file_size = request_params['file_size']
    print(file_name,file_content_type,file_md5,file_path,file_size)

    ip_address = request.META.get('HTTP_X_REAL_IP') or request.META.get('HTTP_REMOTE_ADD')
    #---- Save file to upload file path

    file_suffix = file_name.split('.')[-1]
    new_file_name = get_random_str() + '.' + file_suffix
    new_file_path = ''.join([UPLOAD_FILE_PATH, new_file_name])


    print('1--------------1')
    print(UPLOAD_FILE_PATH)


    #---- Check the file suffix
    if file_suffix not in allow:
        response = HttpResponse("the " + file_suffix + " File was not allowed to upload", content_type='application/json; charset=utf-8')
        return response
    print('2--------------2')
#    #---- if the file was base64 encryption
#    if re.search('base64',file_content_type):
#        print('2.1------------2.1')
#        with open(new_file_path,'ab') as new_file:
#            with open(file_path,'rb') as f:
#                try:
#                    new_file.write(base64.b64decode(f.read()))
#                except Exception as e:
#                    print(e)
#    else:
    #---- Rewrite the file to upload path
    with open(new_file_path, 'ab') as new_file:
        with open(file_path, 'rb') as f:
            try:
                new_file.write(f.read())
            except Exception as e:
                print(e)


    print('3--------------3')
    #---- Check the file MIME Type
    file_mime = magic.from_file(new_file_path,mime=True)
    print('Upload File MIME Type:' + str(file_mime))
    if file_mime not in allow_type:
        os.system('rm -rf ' + new_file_path)
        response = HttpResponse("the " + file_mime + " File was not allowed to upload", content_type='application/json; charset=utf-8')
        return response

    #---- Check the MD5 with the new upload file
    md5_file = open(new_file_path + '.md5sum','a+')
    md5_file.write(file_md5 + '  ' + new_file_name)
    md5_file.close()
    res_md5 = os.system('cd ' + UPLOAD_FILE_PATH + ';' + 'md5sum -c ' + new_file_path + '.md5sum')
    if res_md5 != 0:
        #os.system('rm -rf '+ new_file_path + '*')
        response = HttpResponse("The File :" + file_name + " Fail to pass MD5 Check,Please upload again", content_type='application/json; charset=utf-8')
        return response
    #os.system('ls /home/ap/safm/upload/')
    #os.system('rm -rf '+ new_file_path + '.md5sum')

    content = json.dumps({
        'name': file_name,
        'content_type': file_content_type,
        'md5': file_md5,
        'path': file_path,
        'size': file_size,
        'ip': ip_address,
    })
    print(new_file_path)
    #path_dir = new_file_path.split('/')[1:]
    #res = '/'.join(path_dir)
    #download_url = '/'.join(('http://192.168.110.78:8012',res))
    
    response = HttpResponse("File has been Uploaded\nOriginal file : "+ file_name + "\nNew file : " + new_file_name, content_type='application/json; charset=utf-8')

    return response
