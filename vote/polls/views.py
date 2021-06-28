from django.shortcuts import render, redirect

from polls.captcha import Captcha
from polls.models import Subject, Teacher, User
from polls.serializers import SubjectSerializer, TeacherSerializer, SubjectSimpleSerializer
from polls.utils import gen_random_code, gen_md5_digest

from django.http import JsonResponse,HttpRequest,HttpResponse, request
from rest_framework.decorators import api_view
from rest_framework.response import Response
from urllib.parse import quote

import xlwt
from io import BytesIO

import tkinter
import io

# def show_subjects(request):
#     subjects = Subject.objects.all().order_by('no')
#     return render(request, 'subjects.html', {'subjects': subjects})

def show_index(requests: HttpRequest) -> HttpResponse:
    return redirect('static/html/subjects.html')


@api_view(('GET', ))
def show_subjects(request: HttpRequest) -> HttpResponse:
    subjects = Subject.objects.all().order_by('no')
    # 创建序列化器对象并指定要序列化的模型
    serializer = SubjectSerializer(subjects, many=True)
    # 通过序列化器的data属性获得模型对应的字典并通过创建Response对象返回JSON格式的数据
    return Response(serializer.data)


@api_view(('GET',))
def show_teachers(request: HttpRequest) -> HttpResponse:
    try:
        sno = int(request.GET.get('sno'))
        subject = Subject.objects.only('name').get(no=sno)
        teachers = Teacher.objects.filter(subject=subject).defer('subject').order_by('no')
        subject_seri = SubjectSimpleSerializer(subject)
        teacher_seri = TeacherSerializer(teachers, many=True)
        return Response({'subject': subject_seri.data, 'teachers': teacher_seri.data})
    except (TypeError, ValueError, Subject.DoesNotExist):
        return Response(status=404)

# def show_teachers(request):
#     try:
#         sno = int(request.GET.get('sno'))
#         teachers = []
#         if sno:
#             subject = Subject.objects.only('name').get(no=sno)
#             teachers = Teacher.objects.filter(subject=subject).order_by('no')
#         return render(request, 'teachers.html', {
#             'subject': subject,
#             'teachers': teachers
#         })
#     except (ValueError, Subject.DoesNotExist):
#         return redirect('/')
def praise_or_criticize(request):
    """好评"""
    if request.session.get('userid'):
        try:
            tno = int(request.GET.get('tno'))
            teacher = Teacher.objects.get(no=tno)
            if request.path.startswith('/praise'):
                teacher.good_count += 1
                count = teacher.good_count
            else:
                teacher.bad_count += 1
                count = teacher.bad_count
            teacher.save()
            data = {'code': 20000, 'mesg': '操作成功', 'count': count}
        except (ValueError, Teacher.DoseNotExist):
            data = {'code': 20001, 'mesg': '操作失败'}
    else:
        data = {'code': 20002, 'mesg': '请先登录'}    
    return JsonResponse(data)  


def login(request: HttpRequest) -> HttpResponse:
    hint = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username and password:
            password = gen_md5_digest(password)
            user = User.objects.filter(username=username, password=password).first()
            if user:
                request.session['userid'] = user.no
                request.session['username'] = user.username
                return redirect('/')
            else:
                hint = '用户名或密码错误'
        else:
            hint = '请输入有效的用户名和密码'
    return render(request, 'login.html', {'hint': hint})  


def get_captcha(request: HttpRequest) -> HttpResponse:
    """验证码"""
    captcha_text = gen_random_code()
    request.session['captcha'] = captcha_text
    image_data = Captcha.instance().generate(captcha_text)
    return HttpResponse(image_data, content_type='image/png')

def logout(request):
    """注销"""
    request.session.flush()
    return redirect('/')

def export_teachers_excel(request):
    # 创建工作簿
    wb = xlwt.Workbook()
    # 添加工作表
    sheet = wb.add_sheet('老师信息表')
    # 查询所有老师的信息
    queryset = Teacher.objects.all()
    # 向Excel表单中写入表头
    colnames = ('姓名', '介绍', '好评数', '差评数', '学科')
    for index, name in enumerate(colnames):
        sheet.write(0, index, name)
    # 向单元格中写入老师的数据
    props = ('name', 'detail', 'good_count', 'bad_count', 'subject')
    for row, teacher in enumerate(queryset):
        for col, prop in enumerate(props):
            value = getattr(teacher, prop, '')
            if isinstance(value, Subject):
                value = value.name
            sheet.write(row + 1, col, value)
    # 保存Excel
    buffer = BytesIO()
    wb.save(buffer)
    # 将二进制数据写入响应的消息体中并设置MIME类型
    resp = HttpResponse(buffer.getvalue(), content_type='application/vnd.ms-excel')
    # 中文文件名需要处理成百分号编码
    filename = quote('老师.xls')
    # 通过响应头告知浏览器下载该文件以及对应的文件名
    resp['content-disposition'] = f'attachment; filename*=utf-8\'\'{filename}'
    return resp

def export_pdf(request: HttpRequest) -> HttpResponse:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.setFont("Helvetica", 80)
    pdf.setFillColorRGB(0.2, 0.5, 0.3)
    pdf.drawString(100, 550, 'hello, world!')
    pdf.showPage()
    pdf.save()
    resp = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    resp['content-disposition'] = 'inline; filename="demo.pdf"'
    return resp
def get_teachers_data(request):
    queryset = Teacher.objects.all()
    names = [teacher.name for teacher in queryset]
    good_counts = [teacher.good_count for teacher in queryset]
    bad_counts = [teacher.bad_count for teacher in queryset]
    return JsonResponse({'names': names, 'good': good_counts, 'bad': bad_counts})

from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(('GET', ))
def show_subjects(request: HttpRequest) -> HttpResponse:
    subjects = Subject.objects.all().order_by('no')
    # 创建序列化器对象并指定要序列化的模型
    serializer = SubjectSerializer(subjects, many=True)
    # 通过序列化器的data属性获得模型对应的字典并通过创建Response对象返回JSON格式的数据
    return Response(serializer.data)

from polls.snscode import *

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_redis import get_redis_connection
@api_view(('GET', ))
def get_mobilecode(request, tel):
    """获取短信验证码"""
    if check_tel(tel):
        redis_cli = get_redis_connection()
        if redis_cli.exists(f'vote:block-mobile:{tel}'):
            data = {'code': 30001, 'message': '请不要在60秒内重复发送短信验证码'}
        else:
            code = random_code()
            send_mobile_code(tel, code)
            # 通过Redis阻止60秒内容重复发送短信验证码
            redis_cli.set(f'vote:block-mobile:{tel}', 'x', ex=60)
            # 将验证码在Redis中保留10分钟（有效期10分钟）
            redis_cli.set(f'vote2:valid-mobile:{tel}', code, ex=600)
            data = {'code': 30000, 'message': '短信验证码已发送，请注意查收'}
    else:
        data = {'code': 30002, 'message': '请输入有效的手机号'}
    return Response(data)

import requests
def send_mobile_code(tel, code):
    """发送短信验证码"""
    resp = requests.post(
        url='http://sms-api.luosimao.com/v1/send.json',
        auth=('api', 'key-自己的APIKey'),
        data={
            'mobile': tel,
            'message': f'您的短信验证码是{code}，打死也不能告诉别人哟。【Python小课】'
        },
        verify=False
    )
    return resp.json()

import qiniu

AUTH = qiniu.Auth('qFUT5MVsJRufyjsCx-WhSlUsHLO7IN9IKncn_T5L', 'amgZx008TPheAYmfCFcNYhrD7c7p6kUFfFY1geEy')
BUCKET_NAME = 'voteceshi'


def upload_file_to_qiniu(key, file_path):
    """上传指定路径的文件到七牛云"""
    token = AUTH.upload_token(BUCKET_NAME, key)
    return qiniu.put_file(token, key, file_path)


def upload_stream_to_qiniu(key, stream, size):
    """上传二进制数据流到七牛云"""
    token = AUTH.upload_token(BUCKET_NAME, key)
    return qiniu.put_stream(token, key, stream, None, size)
from django.views.decorators.csrf import csrf_exempt

import os
import uuid
@csrf_exempt
def upload(request):
    # 如果上传的文件小于2.5M，则photo对象的类型为InMemoryUploadedFile，文件在内存中
    # 如果上传的文件超过2.5M，则photo对象的类型为TemporaryUploadedFile，文件在临时路径下
    photo = request.FILES.get('photo')
    _, ext = os.path.splitext(photo.name)
    # 通过UUID和原来文件的扩展名生成独一无二的新的文件名
    filename = f'{uuid.uuid1().hex}{ext}'
    # 对于内存中的文件，可以使用上面封装好的函数upload_stream_to_qiniu上传文件到七牛云
    # 如果文件保存在临时路径下，可以使用upload_file_to_qiniu实现文件上传
    upload_stream_to_qiniu(filename, photo.file, photo.size)
    return redirect('/static/html/upload.html')