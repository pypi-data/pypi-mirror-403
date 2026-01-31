
import glob
import os
from PIL import Image

class GifConverter:
    """
    여러 PNG 이미지를 하나의 GIF로 변환하는 클래스
    - 투명 PNG 지원
    - 프레임 겹침 방지(disposal=2)
    - 리사이즈 옵션 제공
    """    
    
    def __init__(self, path_in=None, path_out=None, resize=(320, 240)):
        """
        patn_in : 원본 여러 이미지 경로
        path_out : 결과 이미지 경로(Ex : output/filename.gif )
        resize : 리사이징 크기((320,240))
        """
        self.path_in = path_in or './*.png'
        self.path_out = path_out or './output.gif'
        self.resize = resize
        
    def convert_git(self):
        """
        GIF 이미지 변환 기능 수행
        """
        print(self.path_in, self.path_out, self.resize)
        
        files = sorted(glob.glob(self.path_in))
        if not files:
            raise RuntimeError("이미지 없음")

        resample = Image.Resampling.LANCZOS

        frames = []
        for f in files:
            img = Image.open(f).convert("RGBA")
            img = img.resize(self.resize, resample=resample)
            frames.append(img)

        msg, *images = frames
        
        try:
            msg.save(
                self.path_out,
                format="GIF",
                save_all=True,
                append_images=images,
                duration=500,
                loop=0,
                disposal=2,      # ⭐ 핵심
                transparency=0
            )
        except IOError:
            print('Cannot conver!', img)

if __name__ == '__main__':            
    c = GifConverter('./project/images/*.png', './project/image_out/result.gif', (320,240))
    c.convert_git()
    print(GifConverter.__doc__)
    print(GifConverter.__init__.__doc__)

