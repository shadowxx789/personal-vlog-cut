# 第三方资源

## FluidR3_GM.sf2
- 用途：scripts/gen_bgm_guitar.py 的吉他音色（GM 24 尼龙、25 钢弦）
- 作者：Frank Wen
- 许可：MIT（许可文本见下，从安装包 copyright 文件复制）
- 来源：Debian .deb 解包（fluid-soundfont-gm_3.1-5.3_all.deb，packages.debian.org / ftp.debian.org 官方镜像 pool/main/f/fluid-soundfont/）
- 本机路径：通过环境变量 PVC_SF2 指定，不入库（.gitignore: *.sf2）；本机为 ~/.local/share/soundfonts/FluidR3_GM.sf2
- sha256：74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0
- 大小：148398306 bytes（141 MB）
- fluidsynth 版本：FluidSynth runtime version 2.6.1（Homebrew）

许可原文（usr/share/doc/fluid-soundfont-gm/copyright）：

```
This package was debianized by Toby Smithe <tsmithe@ubuntu.com> on
Fri, 08 Feb 2008 00:08:09 +0000.

It was downloaded from 
<http://www.musescore.org/download/fluid-soundfont.tar.gz>

Upstream Author: 

    Frank Wen <getfrank@gmail.com>
    
Copyright: 

    Copyright © 2000-2002, 2008 Frank Wen
    Copyright © 2008 Toby Smithe
    
Contributors (quoting from README):

"Fluid was constructed in part from samples found in the public domain that I
edited/cleaned/remixed/programmed and largely from recordings of my own and
in conjunction with the people below who helped along the way:

Suren M. Seron
Scott Hanan
Steve Aupperle
Chris Gillman
Alex Taubr
Chris Prola
Andrew Klenk
Winfried Hubbe 
Dylan
Tim
Gort
Uros Katic 
Ethan Winer (http://www.ethanwiner.com)"

License:

 From README: 
  "I hereby release Fluid under the MIT license, as described in COPYING."

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.

The Debian packaging is Copyright © 2008 Toby Smithe <tsmithe@ubuntu.com> and
is licensed under the GPL; either version 2 of the License, or (at your
option) any later version, see `/usr/share/common-licenses/GPL-2'.
```
