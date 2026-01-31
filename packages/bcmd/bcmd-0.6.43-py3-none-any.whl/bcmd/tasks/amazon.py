import asyncio
import json
import re
import webbrowser
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Final

import pyperclip
import typer
from beni import bcolor, bfile, bhttp, bpath, bplaywright, btask
from beni.bfunc import crcStr, splitWords, syncCall
from beni.block import limit


app: Final = btask.newSubApp('Amazon 工具')


@app.command()
@syncCall
async def open_asin_list(
    asin_list: list[str] = typer.Argument([], help='支持多个 ASIN 使用空格间隔，如果不填写则使用剪贴板内容')
):
    '根据 ASIN 打开多个 Amazon 多个产品页'
    if asin_list:
        print('当前使用命令行参数')
    else:
        print('当前使用剪贴板内容作为参数')
        asin_list = splitWords(pyperclip.paste())
    btask.assertTrue(asin_list, '没有提供任何 ASIN')
    for x in asin_list:
        url = f'https://www.amazon.com/dp/{x}'
        print(url)
        webbrowser.open_new_tab(url)


@app.command()
@syncCall
async def make_part_number():
    '''
    根据 SKU 生成 Part Number
    支持同时成成多个，这里使用粘贴板里的内容作为参数，每行代表1个SKU
    原理：将 SKU 使用 CRC32 生成校验码作为 Part Number
    '''
    content = pyperclip.paste().replace('\r', '')
    ary = content.split('\n')
    resultList: list[str] = []
    for item in ary:
        item = item.strip()
        result = ''
        if item and '-' in item:
            # key = '-'.join(item.split('-')[:-1])
            key = item
            result = crcStr(key).upper()
        resultList.append(result)
        print(item, '=>', result)
    outputContent = '\n'.join(resultList)
    pyperclip.copy(outputContent)
    bcolor.printGreen('Part Number 已复制到剪贴板')
    bcolor.printGreen('OK')


@app.command()
@syncCall
async def download_images(
    output_path: Path = typer.Argument(Path.cwd(), help='指定目录或具体图片文件，默认当前目录'),
):
    '''
    下载亚马逊产品图片
    包括第一张主图以及全部评论的图片
    以目录作为一个操作单位，里面支持有一个可选的 urls.txt 文件，里面包含多个产品链接，每行一个
    里面有一个 info.json 文件，记录需要解析的url以及需要下载的图片链接
    '''

    urlsFile = output_path / 'urls.txt'
    infoFile = output_path / 'info.json'

    @dataclass
    class Info():

        asin_list: list[str] = field(default_factory=list)
        asin_done_list: list[str] = field(default_factory=list)
        img_url_list: list[str] = field(default_factory=list)
        _isAutoSave: bool = False
        _dataCrc: str = ''

        @classmethod
        async def load(cls):
            if infoFile.is_file():
                try:
                    data: dict[str, Any] = await bfile.readJson(infoFile)
                    allowed = {f.name for f in cls.__dataclass_fields__.values()}
                    cleaned = {k: v for k, v in data.items() if k in allowed and not k.startswith('_')}
                    return cls(**cleaned)
                except Exception as e:
                    btask.abort('请修复 info.json 后重试', str(e))
            return cls()

        async def save(self) -> None:
            data = {k: v for k, v in asdict(self).items() if not k.startswith('_')}
            dataStr = json.dumps(data, ensure_ascii=False, indent=4, sort_keys=True)
            if crcStr(dataStr) != self._dataCrc:
                self._dataCrc = crcStr(dataStr)
                await bfile.writeText(infoFile, dataStr)

        async def autoSave(self, delay: int = 3) -> None:
            if not self._isAutoSave:
                self._isAutoSave = True
                while self._isAutoSave:
                    await asyncio.sleep(delay)
                    await self.save()

        def stopAutoSave(self) -> None:
            self._isAutoSave = False

    # 初始化数据
    info = await Info.load()
    infoAutoSaveTask = asyncio.create_task(info.autoSave())
    downloadTaskList: list[asyncio.Task[None]] = []

    # 读取 urls 文件，将数据写入 info
    if not urlsFile.is_file():
        await bfile.writeText(urlsFile, '')
    content = await bfile.readText(urlsFile)
    asin_matches = re.findall(r'/dp/([A-Z0-9]{10})', content, re.IGNORECASE)
    newAsinList = list(set(dict.fromkeys(asin_matches)) - set(info.asin_list) - set(info.asin_done_list))
    if newAsinList:
        info.asin_list.extend(newAsinList)
        info.asin_list.sort()
        print(f'新增 {len(newAsinList)} 个 ASIN：{' '.join(newAsinList)}')

    @limit(5)
    async def downloadImage(url: str) -> None:
        file = output_path / bpath.get(url).name
        if not file.is_file():
            try:
                await bhttp.download(url, file)
                info.img_url_list.remove(url)
                print('下载完成', url)
            except:
                bcolor.printRed('下载失败', url)

    # 先下载 info 里面已经存在的图片链接（上次没有进行的或下载失败的链接）
    for imgUrl in info.img_url_list:
        downloadTaskList.append(asyncio.create_task(downloadImage(imgUrl)))

    # 使用 playwright 解析图片链接
    async with bplaywright.page(
        browser={
            # 'headless': False,  # 显示浏览器UI
            'channel': 'chrome',  # 使用系统 Chrome 浏览器
        }
    ) as page:
        asinList = info.asin_list[:]
        for asin in asinList:
            try:
                productUrl = f'https://www.amazon.com/dp/{asin}'
                await page.goto(productUrl)

                # 如果出现验证界面则点击等待后继续
                continueShopping = page.get_by_text('Continue shopping')
                if await continueShopping.count():
                    await continueShopping.last.click()
                    await page.wait_for_load_state('load')

                # 收集第一张主图
                mainImg = page.locator('#landingImage')
                mainImgUrl = await mainImg.get_attribute('src')
                assert mainImgUrl, '无法找到主图链接'
                oldStem = bpath.get(mainImgUrl).stem
                newStem = oldStem.split('.')[0]
                mainImgUrl = mainImgUrl.replace(oldStem, newStem)
                info.img_url_list.append(mainImgUrl)
                downloadTaskList.append(
                    asyncio.create_task(downloadImage(mainImgUrl))
                )

                # 获取评论里面的图片链接
                seeAllPhotosBtn = page.get_by_text('See all photos')
                if await seeAllPhotosBtn.count() == 0:
                    seeAllPhotosBtn = page.get_by_text('查看所有照片')
                if await seeAllPhotosBtn.count():
                    async with page.expect_response(lambda r: "getGroupedMediaReviews" in r.url and r.ok) as resp_info:
                        await seeAllPhotosBtn.click()
                    resp = await resp_info.value
                    data = await resp.json()
                    for group in data['mediaGroupList']:
                        for media in group['mediaList']:
                            if media['mediaType'] == 'IMAGE':
                                imgUrl = media['image']['url']
                                if imgUrl in info.img_url_list:
                                    bcolor.printYellow('放弃重复的图片链接A', imgUrl)
                                    continue
                                targetFile = output_path / bpath.get(imgUrl).name
                                if targetFile.is_file():
                                    bcolor.printYellow('放弃重复的图片链接B', imgUrl)
                                    continue
                                print('收集图片链接', imgUrl)
                                info.img_url_list.append(imgUrl)
                                downloadTaskList.append(
                                    asyncio.create_task(downloadImage(imgUrl))
                                )
                else:
                    bcolor.printYellow('没有站到任何评论照片')

                # 将 ASIN 标记为已完成
                info.asin_done_list.append(asin)
                info.asin_list.remove(asin)

            except Exception as e:
                bcolor.printRed('网页分析失败', asin, str(e))

    # 等待下载完成
    await asyncio.gather(*downloadTaskList)

    # 停止数据的自动保存
    info.stopAutoSave()
    await infoAutoSaveTask

    bcolor.printGreen('OK')
