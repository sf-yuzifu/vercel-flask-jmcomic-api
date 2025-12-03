from io import BytesIO
from flask import Flask, Response, jsonify, request
from jmcomic import *

import sys

sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)
app.debug = False
app.json.ensure_ascii = False

# 存储捕获的图片
captured_images = {}

# 保存原始的save_image方法
original_save_image = JmImageTool.save_image


@classmethod
def new_save_image(cls, image: Image.Image, filepath: str):
    """
    新的save_image方法，捕获PIL.Image对象
    """
    # 捕获图片对象
    captured_images[filepath] = image

    # 调用原始方法保存文件
    # return original_save_image(image, filepath)


JmImageTool.save_image = new_save_image

# original_try_mkdir = JmcomicText.try_mkdir


@classmethod
def new_try_mkdir(cls, save_dir: str):
    return save_dir


JmcomicText.try_mkdir = new_try_mkdir

from urllib.parse import unquote, quote
import re


def decode_search_value(value: str) -> str:
    """
    判断并解码搜索值
    如果值是URL编码，则解码为中文，否则直接返回
    """
    # URL编码的特征：包含%后跟两个十六进制字符
    url_encoded_pattern = r"%[0-9A-Fa-f]{2}"

    # 如果包含URL编码特征，尝试解码
    if re.search(url_encoded_pattern, value):
        try:
            decoded = unquote(value)
            # 解码后如果还包含URL编码特征，说明可能有多重编码，继续解码
            while re.search(url_encoded_pattern, decoded):
                temp = unquote(decoded)
                if temp == decoded:  # 如果没有变化，停止解码
                    break
                decoded = temp
            return decoded
        except Exception:
            # 如果解码失败，返回原值
            return value
    else:
        # 没有URL编码特征，直接返回
        return value


@app.get("/")
def read_root():
    return """
it works!
    """


@app.get("/album/<int:item_id>/cover")
def get_album_cover(item_id: int):
    """返回封面响应"""
    try:
        a = JmOption.default().new_jm_client()

        a.download_album_cover(item_id, "./cover.webp", "_3x4")

        # 检查是否捕获到图片
        if not captured_images:
            return jsonify({"code": 404, "message": "No image captured"}), 404

        # 获取第一个捕获的图片
        image = next(iter(captured_images.values()))
        captured_images.clear()  # 清空捕获的图片

        # ========== 图片压缩和尺寸限制 ==========
        # 获取原始尺寸
        original_width, original_height = image.size
        print(f"原始图片尺寸: {original_width}x{original_height}")

        # 设置最大宽度
        width = request.args.get("w")
        max_width = int(width) if width and width.isdigit() else 100

        if original_width > max_width:
            # 计算等比例缩放后的高度
            new_height = int((max_width / original_width) * original_height)
            # 使用高质量的重采样算法
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            print(f"压缩后尺寸: {max_width}x{new_height}")
        else:
            print(f"图片宽度 {original_width}px 已小于限制 {max_width}px，无需压缩")

        # 进一步优化图片质量和大小
        optimize_options = {
            "quality": 50,  # 降低质量到50%
            "optimize": True,  # 启用优化
            "progressive": True,  # 启用渐进式JPEG（对大图加载友好）
        }

        # 如果是PNG或WEBP格式，转换为JPEG以进一步减小体积
        if image.mode in ["RGBA", "P"]:
            # 创建白色背景
            background = Image.new("RGB", image.size, (255, 255, 255))
            # 如果有透明通道，将图片粘贴到白色背景上
            if image.mode == "RGBA":
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            else:
                background.paste(image)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 将PIL.Image转换为字节流
        img_io = BytesIO()

        # 保存为JPEG格式到内存（应用压缩设置）
        image.save(img_io, "JPEG", **optimize_options)

        # 获取压缩后的大小
        compressed_size = img_io.tell()
        img_io.seek(0)

        print(f"压缩后文件大小: {compressed_size / 1024:.1f} KB")

        # 返回图片响应
        return Response(
            img_io.getvalue(),
            mimetype="image/jpeg",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600",
                "X-Image-Original-Size": f"{original_width}x{original_height}",
                "X-Image-Compressed-Size": f"{image.size[0]}x{image.size[1]}",
                "X-Image-File-Size": str(compressed_size),
            },
        )

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.get("/search/<value>")
@app.get("/search/<value>/")
@app.get("/search/<value>/<int:client_page>")
def get_search(value, client_page=1):
    try:
        client = JmOption.default().new_jm_client()

        search_keyword = decode_search_value(value)
        print(f"原始值: {value}, 解码后: {search_keyword}")

        # 客户端分页设置
        client_page_size = 10
        # API分页设置
        api_page_size = JmModuleConfig.PAGE_SIZE_SEARCH

        # 计算对应的API页码
        # 公式解释: 客户端第N页的起始数据编号为 (N-1)*client_page_size + 1
        # 这个编号在哪个API页呢？用这个编号除以API每页大小，再向上取整。
        api_page = ((client_page - 1) * client_page_size) // api_page_size + 1

        # 计算在该API页内的起始索引 (从0开始)
        start_index_in_api_page = ((client_page - 1) * client_page_size) % api_page_size

        # 请求对应的API页面
        page: JmSearchPage = client.search_site(
            search_query=search_keyword, page=api_page
        )

        # 收集当前API页的所有结果
        all_results_in_api_page = []
        for album_id, title in page:
            all_results_in_api_page.append({"album_id": album_id, "title": title})

        # 从API页结果中截取客户端需要的那10条
        end_index_in_api_page = start_index_in_api_page + client_page_size
        client_results = all_results_in_api_page[
            start_index_in_api_page:end_index_in_api_page
        ]

        # 计算客户端总页数 (基于API报告的总数)
        total_client_pages = (page.total + client_page_size - 1) // client_page_size

        return jsonify(
            {
                "client_page_size": client_page_size,
                "client_page_count": total_client_pages,
                "current_client_page": client_page,
                "current_api_page": api_page,
                "start_index_in_api_page": start_index_in_api_page,
                "results": client_results,
            }
        )

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.get("/album/<int:item_id>/info")
def get_album_info(item_id: int, impl="html", url=["18comic.vip"]):
    try:
        a = JmOption.construct(
            {
                "client": {
                    "domain": url,
                    "impl": impl,
                },
                "plugins": {
                    "after_init": [
                        {
                            "plugin": "login",
                            "kwargs": {
                                "username": "test19195456546",
                                "password": "test19195456546",
                            },
                        }
                    ]
                },
            }
        )
        # 客户端
        client = a.new_jm_client(impl=impl)
        # 本子实体类
        album: JmAlbumDetail = client.get_album_detail(item_id)

        photo_detail = client.get_photo_detail(item_id)
        total_pages = len(photo_detail)

        return jsonify(
            {
                "item_id": item_id,
                "name": album.name,
                "actors": album.actors,
                "page_count": total_pages,
                "tags": album.tags,
                "authors": album.authors,
                "pub_date": album.pub_date,
                "description": album.description,
                "views": album.views,
                "update_date": album.update_date,
                "likes": album.likes,
                "comment_count": album.comment_count,
            }
        )
    except Exception as e:
        if str(e).find("只对登录用户可见") != -1 and impl != "api":
            print("只对登录用户可见", str(e))
            return get_album_info(item_id, impl="api", url=[])
        if str(e).find("请求重试全部失败") != -1:
            print("请求重试全部失败", str(e))
            return get_album_info(item_id, url=[])
        return jsonify({"code": 500, "message": str(e)}), 500


@app.get("/photo/<int:item_id>")
@app.get("/photo/<int:item_id>/")
@app.get("/photo/<int:item_id>/<int:page>")
def get_image(item_id: int, page: int = 1):
    """返回图片响应"""
    try:

        class ImageDownloader(JmDownloader):
            def do_filter(self, detail):
                if detail.is_photo():
                    photo: JmPhotoDetail = detail
                    # 支持[start,end,step]
                    return photo[page - 1 : page]
                return detail

        JmModuleConfig.CLASS_DOWNLOADER = ImageDownloader

        # 下载图片
        download_photo(item_id)

        # 检查是否捕获到图片
        if not captured_images:
            return jsonify({"code": 404, "message": "No image captured"}), 404

        print(captured_images)

        # 获取第一个捕获的图片
        image = next(iter(captured_images.values()))
        captured_images.clear()  # 清空捕获的图片

        # ========== 图片压缩和尺寸限制 ==========
        # 获取原始尺寸
        original_width, original_height = image.size
        print(f"原始图片尺寸: {original_width}x{original_height}")

        # 设置最大宽度
        max_width = 600

        if original_width > max_width:
            # 计算等比例缩放后的高度
            new_height = int((max_width / original_width) * original_height)
            # 使用高质量的重采样算法
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            print(f"压缩后尺寸: {max_width}x{new_height}")
        else:
            print(f"图片宽度 {original_width}px 已小于限制 {max_width}px，无需压缩")

        # 进一步优化图片质量和大小
        optimize_options = {
            "quality": 50,  # 降低质量到50%
            "optimize": True,  # 启用优化
            "progressive": True,  # 启用渐进式JPEG（对大图加载友好）
        }

        # 如果是PNG或WEBP格式，转换为JPEG以进一步减小体积
        if image.mode in ["RGBA", "P"]:
            # 创建白色背景
            background = Image.new("RGB", image.size, (255, 255, 255))
            # 如果有透明通道，将图片粘贴到白色背景上
            if image.mode == "RGBA":
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
            else:
                background.paste(image)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 将PIL.Image转换为字节流
        img_io = BytesIO()

        # 保存为JPEG格式到内存（应用压缩设置）
        image.save(img_io, "JPEG", **optimize_options)

        # 获取压缩后的大小
        compressed_size = img_io.tell()
        img_io.seek(0)

        print(f"压缩后文件大小: {compressed_size / 1024:.1f} KB")

        # 返回图片响应
        return Response(
            img_io.getvalue(),
            mimetype="image/jpeg",
            headers={
                "Content-Disposition": "inline",
                "Cache-Control": "public, max-age=3600",
                "X-Image-Original-Size": f"{original_width}x{original_height}",
                "X-Image-Compressed-Size": f"{image.size[0]}x{image.size[1]}",
                "X-Image-File-Size": str(compressed_size),
            },
        )

    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@app.get("/config")
@app.get("/config/")
def config():
    return jsonify(
        {
            "JMComic": {
                "name": "JMComic",
                "apiUrl": "https://jmcomic.yzf.moe",
                "searchPath": "/search/<text>/<page>",
                "detailPath": "/album/<id>/info",
                "photoPath": "/photo/<id>/<page>",
                "coverPath": "/album/<id>/cover",
                "type": "jmcomic",
            },
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
