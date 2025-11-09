from io import BytesIO
from flask import Flask, Response, jsonify
from jmcomic import *

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


@app.get("/")
def read_root():
    return """
it works!
    """


@app.get("/album/<int:item_id>/info")
def get_album_info(item_id: int, impl="html"):
    try:
        a = JmOption.default()
        if a.client.postman.meta_data.get('cookies') is None:
            a.client.postman.meta_data['cookies'] = {}  # 确保cookies字段存在
        a.client.postman.meta_data['cookies']['AVS'] = "1e4m8ifti47229fp476kinhacl716"
        # 客户端
        client = a.new_jm_client(impl=impl)
        # 本子实体类
        album: JmAlbumDetail = client.get_album_detail(item_id)

        return jsonify(
            {
                "item_id": item_id,
                "name": album.name,
                "actors": album.actors,
                "page_count": album.page_count,
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
        if str(e).find("只对登录用户可见") != -1:
            return get_album_info(item_id, impl="api")
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
