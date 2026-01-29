#!/usr/bin/env python
"Accessibility CSS Generator, (c) Silas S. Brown 2006-26.  Version 0.9943"
# Works on either Python 2 or Python 3

# Website: https://ssb22.user.srcf.net/css/

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# CHANGES
# -------
# If you want to compare this code to old versions, the old
# versions are being kept in the E-GuideDog SVN repository on
# http://svn.code.sf.net/p/e-guidedog/code/ssb22/css-generator
# and on GitHub at https://github.com/ssb22/css-generator
# and on GitLab at https://gitlab.com/ssb22/css-generator
# and on BitBucket https://bitbucket.org/ssb22/css-generator
# and at https://gitlab.developers.cam.ac.uk/ssb22/css-generator
# and in China: https://gitee.com/ssb22/css-generator
# as of v0.9782.  Versions prior to that were not kept, but
# some were captured by Internet Archive at
# https://web.archive.org/web/*/http://people.pwf.cam.ac.uk/ssb22/css/css-generate.py

# CONFIGURATION
# -------------

# The default configuration can be changed here, or if you
# prefer you can copy and paste all of this to a separate
# file called css_generate_config.py and edit it there
# (which should make it easier to update the code
# independently of your configuration).
# You can also put a css_generate_config.py into your
# ~/.local/lib/python3*/site-packages or wherever
# else your Python is configured to get its modules.

# Where to put the output CSS files: default is current directory,
# but you might want to put them in a subdirectory, or set
# an absolute path
outputDir = "."

try: True # backward compatibility with Python 2.1:
except: exec("True,False=1,0") # (syntax error in Python 3)

# Whether to write an HTML menu to standard output as well
# (see my CSS page for example)
outHTML = True
# if putting this on the Web, include in .htaccess:
# AddType text/css css
# SetEnvIf Request_URI "\.css$" requested_css=css
# Header add Content-Disposition "Attachment" env=requested_css

# Which pixel sizes to generate.
# Size 0 means "unchanged" - it will disable the size
# changes, and the layout changes that are meant for large
# sizes.  This is for people who need only colour changes,
# or for whom the browser's built-in zoom is sufficient
# (e.g. on a large display and/or complex layouts that
# aren't very-well dealt with by our layout changes).
pixel_sizes_to_generate = [0,18,20,25,30,35,40,45,50,60,75,100]

# Which pixel size to use with the "chop" and related debug options:
chop_pixel_size = 20

# Which colour schemes to generate.  The format of this is
# [("description","filename-prefix",{...}),...]
# - see the existing ones for examples.
# If you have many of these, you might want to read them
# in from separate configuration files instead of listing
# them here.  In that case, set colour_schemes_to_generate
# to a string containing a wildcard,
# e.g. colour_schemes_to_generate = "my_config_dir/*.conf"
# in which case each file in my_config_dir/*.conf should
# contain one or more entries in the same [(...),...] format
# WARNING: this will be passed to Python's eval() function
# which can execute any command, so don't allow an
# untrusted third party to write these *.conf files.

colour_schemes_to_generate = [
  ("yellow on black","",
   {"text":"yellow","background":"black",
    "translucent_background_compromise":"rgba(0,0,0,0.5)",
    "headings":"#8080FF","link":"#00FF00",
    "hover-bkg":"#0000C0","visited":"#00FFFF",
    "bold":"#FFFF80","italic":"white",
    "coloured":"pink", # used for text inside any FONT COLOR= markup
    "button-bkg":"#600040",
    "select-bkg":"#600060",
    "reset-bkg":"#400060",
    "form_disabled":"#404040", # GrayText requires CSS 2.1
    "selection-bkg":"#006080", # (if supported by the browser. BEWARE: Some browsers, e.g. Safari 6, will NOT display this exact colour, but a computed medium mid-way between it and the unselected background; you should therefore ensure that other backgrounds (e.g. highlight) are discernable against those 'computed medium' colours as well)
    "highlight-bkg":"#300030", # (misc non-selection highlights in site-specific hacks)
    "image_transparency_compromise":"#808000" # non-black and non-white background for transparent images, so at least stand a chance of seeing transparent imgs that were meant for white bkg (or black bkg)
    }),
  
  ("green on black","green",
   {"text":"#00FF00","background":"black",
    "translucent_background_compromise":"rgba(0,0,0,0.5)",
    "headings":"#40C080","link":"#008AFF",
    "hover-bkg":"#400000","visited":"#00FFFF",
    "bold":"#80FF80","italic":"white",
    "button-bkg":"#600040",
    "select-bkg":"#600060",
    "coloured":"#80C040",
    "reset-bkg":"#400060",
    "form_disabled":"#404040",
    "selection-bkg":"#4000c0",
    "highlight-bkg":"#003050",
    "image_transparency_compromise":"#808000"
    }),
  
  ("white on black","WonB",
   {"text":"white","background":"black",
    "translucent_background_compromise":"rgba(0,0,0,0.5)",
    "headings":"#40C090","link":"#0080FF",
    "hover-bkg":"#400000","visited":"#00FFFF",
    "bold":"yellow","italic":"#FFFF80",
    "button-bkg":"#600040",
    "select-bkg":"#600060",
    "coloured":"#FFFF40",
    "reset-bkg":"#400060",
    "form_disabled":"#404040",
    "selection-bkg":"#4080c0",
    "highlight-bkg":"#003050",
    "image_transparency_compromise":"#808080"
    }),
  
  ("soft greys","soft", # c.f. Nightshift etc; thanks to Liviu Andronic for testing
   {"text":"#C0C0C0","background":"#383838",
    "translucent_background_compromise":"rgba(56,56,56,0.5)",
    "alt-backgrounds":["#333333","#2E2E2E"], # optional
    "headings":"#40C090","link":"#BDB76B",
    "hover-bkg":"#453436","visited":"#B6AA7B",
    "bold":"#CD853F","italic":"#EFEFCF",
    "button-bkg":"#553030",
    "select-bkg":"#603440",                              
    "coloured":"#E0E040",
    "reset-bkg":"#303055",
    "form_disabled":"#555753",
    "selection-bkg":"#5f5f5f",
    "highlight-bkg":"#2e3050",
    "focusOutlineStyle":"solid #006080",
    "image_opacity":0.8,
    "image_transparency_compromise":"#2e3436"
  }),

  ("black on linen","BonL", # LyX's background colour is "linen", 240/230/220
   {"text":"black","background":"#faf0e6",
    "translucent_background_compromise":"rgba(250,240,230,0.5)",
    "headings":"#404040","link":"#0000FF",
    "hover-bkg":"#80C0C0","visited":"#008020",
    "bold":"black","italic":"#400000",
    "button-bkg":"#608040",
    "select-bkg":"#608060",
    "coloured":"#001040",
    "reset-bkg":"#408060",
    "form_disabled":"#A0A0A0",
    "highlight-bkg":"#FFFFE6",
    "image_transparency_compromise":"#faf0e6"
    }),
  
  ("black on white","BonW", # cld call this "black on bright white" (as opposed to "black on linen white") but that causes the list to take up more width
   {"text":"black","background":"white",
    "translucent_background_compromise":"rgba(255,255,255,0.5)",
    "headings":"#404040","link":"#0000FF",
    "hover-bkg":"#80C0C0","visited":"#008020",
    "bold":"black","italic":"#400000",
    "button-bkg":"#608040",
    "select-bkg":"#608060",
    "coloured":"#001040",
    "reset-bkg":"#408060",
    "form_disabled":"#A0A0A0",
    "highlight-bkg":"#FFFF80",
    "image_transparency_compromise":"white"
    }),
  ]

# Some other options you might want to change:
separate_adjacent_links_at_size_0 = False # sometimes interferes with layouts
separate_adjacent_links_at_other_sizes = True
preapply_FfxDarkModeExceptions = False # or True, or a list of extra domains to which you want to apply them (e.g. internal sites)
override_output_filename=None # or "/path/to/file.css"
# - if override_output_filename is set, only the first of
# colour_schemes_to_generate and pixel_sizes_to_generate
# will apply, and will go to *that* file, implying outHTML=False
# (you can use this to directly update a Firefox profile etc)

# Fonts: (cjk_fonts is listed first so it can be used in both serif_fonts and sans_serif_fonts)
cjk_fonts = "Lantinghei SC, AppleGothic"
# AppleGothic must be listed or Korean is broken on Mac OS 10.7
# Lantinghei SC was introduced to OS X in 10.9, which is handy because the previously-good STSong font (which was the system default for Simplified Chinese) broke on 10.9: it renders badly with antialiasing turned off at 20px, e.g. missing the horizontal stroke on U+95E8.  So we set Lantinghei SC for 10.9 but fall back to STSong on 10.8/10.7/etc (I don't think we need to explicitly say STSong, and there are advantages in not doing so, e.g. the TODO below about :lang(ja) is not relevant for pre-10.9 systems)
# TODO: for :lang(ko) and :lang(ja) we had better put AppleGothic and a Japanese font like YuGothic first (before Lantinghei) - see below re U+8D77, U+95E8 etc.  Pity can't read the system preferences for pages that don't set a CJK value of LANG.  This :lang exception needs to be done separately for every element that has a font-family, to avoid corrupting headings etc.
# Other Mac CJK fonts to be aware of: MingLiU prefers full 'Traditional' forms of characters where Trad/Simp has same Unicode value (e.g. U+8D77 'qi3' has an extra vertical stroke making the 'ji' component look more like a 'si'); renders OK on Mac OS 10.9 at 20px without antialias, but might not always be present (the ttf is installed to /Library/Fonts/Microsoft by MS Office and is not present on machines without MS Office).  Arial Unicode MS (present on both 10.7 and 10.9) has some issues with baselines not lining up e.g. in the word 'zhen1li3' U+771F U+7406; it prefers Simplifed Chinese forms (e.g. U+8D77 uses 'ji', and U+95E8 is the Chinese rather than the Japanese simplification).  GB18030 Bitmap (NISC18030) might work at 16px, 32px etc, but scales badly to other sizes.  "Hei" has irregular stroke widths in 10.9 20px no-antialias, but otherwise OK
serif_fonts = "Times New Roman, times, utopia, /* charter, */ "+cjk_fonts+", serif" # TNR is listed first for the benefit of broken Xft systems that need the MS fonts to make them look OK. Shouldn't have any effect on other systems.
sans_serif_fonts = "helvetica, arial, verdana, "+cjk_fonts+", sans-serif" # (TODO: do we want different cjk_fonts here?)
pinyin_fonts = "FreeSerif, Lucida Sans Unicode, Times New Roman, DejaVu Sans, serif" # try to get clear tone marks (but DejaVu Sans must be low priority because it results in disappearing text on some buggy Safari versions under Mac OS 10.7)

browser_is_Firefox_73 = False # set this to True ONLY if you are using Firefox 73, to work around bug 1616243.  Do NOT set it to True on Firefox 74+ as it will make checkboxes unreadable.

extra_CSS = "" # so you can add more in css_generate_config.py

# ---- End of options (but read on for debugging) ----

# DEBUGGING BY BINARY CHOP: If a complex stylesheet exhibits
# a behaviour you weren't expecting (maybe due to a browser
# bug but maybe not) then it might not be obvious how to fix
# it.  This program has a debug mode that helps you do it by
# binary chop.  Run like this:
#    python -m css_generate chop
# which will generate a single debug .css file with half
# the attributes disabled.  Try that debug .css; if the
# problem persisted, then do
#    python -m css_generate chop 1
# or if the problem did not persist, do
#    python -m css_generate chop 0
# and then try again.  Then add another 1 or 0 depending on
# whether or not the problem persisted the next time, e.g.
#    python -m css_generate chop 01
# Hopefully it will narrow down the problem to one thing.
# You will see which one that is from the debug messages
# it prints on standard output (these will appear instead of
# the HTML index of stylesheets that is usually generated).
chop_extra_verification = True # If True, we'll take an extra step to verify each chop result (by checking we get the opposite in the inverse set) before further subdivisions

# For more desperate debugging cases, you can try:
#    python -m css_generate desperate-debug
# which will generate a large number of stylesheets, each
# adding one more rule and not combining.  (Note that some
# rules at the beginning and end of the stylesheet will be
# there unconditionally though.)

# TODO consider forcing "display" to its normal value (not "none")
# if some sites are going to use stock scripts that switch them on and
# off every few seconds inadvertently making the rest of the page dance around

# ---- End of debugging info, code follows ----

try: from css_generate_config import *
except ImportError: pass

try: any
except: # backward compatibility with Python 2.1:
  def any(l):
    for i in l:
      if i: return True
try: dict
except:
  def dict(l):
    r = {}
    for k,v in l:
      r[k] = v
    return r
try: set
except:
  def set(l): return l
try: sorted
except:
  def sorted(l,cmpFunc=None):
    r = l[:]
    r.sort(cmpFunc)
    return r
try: reduce # Python 2
except: # Python 3
  from functools import reduce, cmp_to_key
  _builtin_sorted = sorted
  def sorted(l,theCmp=None):
    if theCmp: return _builtin_sorted(l,key=cmp_to_key(theCmp))
    else: return _builtin_sorted(l)
  def cmp(a,b): return (a>b)-(a<b)
try: bytes # Python 3 and newer Python 2
except: bytes = str # older Python 2
try: unicode # Python 2
except: unicode = str # Python 3

if type(colour_schemes_to_generate) in (str,unicode):
  import glob
  colour_schemes_to_generate = reduce(lambda x,y:x+eval(open(y).read()), glob.glob(colour_schemes_to_generate), [])

def do_one_stylesheet(pixelSize,colour,filename,debugStopAfter=0):
  if filename.startswith(os.sep): fn=filename # e.g. override_output_filename
  else: fn=outputDir+os.sep+filename
  outfile = open(fn,"w")
  smallestHeadingSize = pixelSize*5.0/6.0
  largestHeadingSize = pixelSize*10.0/6.0

  # In the settings below, beginning with * means it will
  # be omitted from the "pixelSize 0" option (i.e. leave
  # site's size/layout alone and just changing colours),
  # and anything beginning with ** means it will be
  # included ONLY in the "pixelSize 0" option.
  defaultStyle={
    "*font-family":serif_fonts,
    "*font-size":"%.1fpx" % pixelSize,
    "color":colour["text"],
    "background":colour["background"], # background-color is handled by aliases
    # We have to specify more or less everything even if
    # it's OK by default, otherwise a web author's
    # stylesheet may override the default and cause a
    # not-so-good author/user stylesheet combination.
    "*font-style":"normal",
    "*font-weight":"normal",
    "*font-variant":"normal",
    "*font-size-adjust":"none",
    "*zoom":"normal", # MSIE thing; some other browsers understand it too; can give websites another chance to shrink the text if we don't set it here
    "background-image":"none",
    "*letter-spacing":"normal",
    "*line-height":"normal",
    "*width":"auto",
    "*height":"auto",
    "*border-width":"0.05em",
    "*border-radius":"0.05em",
    "*-moz-border-radius":"0.05em",
    "*-webkit-border-radius":"0.05em",
    "*-webkit-font-smoothing":"none", # font smoothing doesn't work so well on large-print low-resolution dark-background displays...
    "*-moz-osx-font-smoothing":"auto","*font-smooth":"never", # -moz-osx-font-smoothing overrides font-smooth on Firefox 25+; "never" would be better, but at least Ffx 29 and 45.9-ESR doesn't support it and falls back to the SITE's spec :-( (greyscale is worse than auto in large print low resolution) (only auto and greyscale are supported in firefox-45.0esr/layout/style/nsCSSProps.cpp, see gfx/thebes/gfxMacFont.cpp the only way to turn it off is if it's 12pt or smaller and you've said so in Apple Preferences and enabled about:config's gfx.use_text_smoothing_setting; still no good for over 12pt)
    "*-webkit-text-stroke":"0",
    "*-webkit-animation":"none","*-o-animation":"none","*-moz-animation":"none","*animation":"none",
    "*-webkit-animation-name":"none","*-o-animation-name":"none","*-moz-animation-name":"none","*animation-name":"none",
    "*position":"static",
    "*visibility":"visible", # because we're forcing position to static, we must also force visibility to visible otherwise will get large gaps.  Unfortunately some authors use visibility:hidden when they should be using display:none, and CSS does not provide a way of saying '[visibility=hidden] {display:none}'
    "*float":"none","*clear":"none",
    "*min-height":"0px",
    "*max-height":"none",
    "*max-width":"none", # see comments below on "max-width"
    "*min-width":"0px",
    "*text-decoration":"none",
    "text-shadow":"none",
    "mix-blend-mode":"normal",
    "*text-align":"left", # not full justification
    "*margin":"0px",
    "*padding":"0px",
    "*text-indent":"0px",
    "*white-space":"normal", # not "nowrap"
    "*cursor":"auto",
    "*overflow":"visible", # the default.  NOT "auto" - it may put the scroll bar of a table off-screen at the bottom.  If (e.g.) "pre" overflows, we want the whole window to be scrollable to see it.
    
    "filter":"none","-webkit-filter":"none","-moz-filter":"none","-o-filter":"none","-ms-filter":"none", # don't allow 'invert' etc unless we say
    "*opacity":"1",
    "*mask-image":"none","*-webkit-mask-image":"none",
    
    "-moz-appearance":"none", # DON'T * this, it can lead to white-on-white situations so we need it for colour changes not just size changes

    "*-webkit-hyphens":"manual", # auto hyphenation doesn't always work very well with our fonts (TODO: manual or none?  manual might be needed if devs put breakpoints into very long words)
    "*-moz-hyphens":"manual",
    "*-ms-hyphens":"manual",
    "*hyphens":"manual",
    "*table-layout":"auto",
    "user-select":"text","-moz-user-select":"text","-webkit-user-select":"text", # don't allow making things non-selectable, as selection might help keep track of things (TODO: still have user-select:none for buttons etc?)
    "*flex-wrap":"wrap", # needed for giant print or small windows
    "*grid-column-start":"auto","*grid-column-end":"auto","*grid-row-start":"auto","*grid-row-end":"auto",
    "*grid-auto-columns":"auto","*grid-auto-rows":"auto","*grid-auto-flow":"row",
    "*grid-template-columns":"none","*grid-template-rows":"none",
    "*justify-content":"flex-start","*align-items":"flex-start","*align-content":"flex-start","*align-self":"flex-start", # hopefully makes things more findable
    "*flex-basis":"auto", # giant print or small windows can cause long words to overflow 'flex' layouts that specify small pixel widths
    "*flex":"0 1 auto", # may prevent margin overflow
    "*-moz-column-count":"1", # see below for column-count (NOT webkit, Chrome/57 bug)
    }
  for css3Thing,value in [
      # Get rid of "flip boxes"...
      ("transform","none"),
      ("transform-style","flat"),
      ("backface-visibility","visible"),
      ("transition-property","none")]:
    for browser in ["",'-o-','-ms-','-moz-','-webkit-']:
      defaultStyle['*'+browser+css3Thing] = value

  # have to explicitly set for every type of element,
  # because wildcards don't always work and inheritance can
  # be overridden by author stylesheets resulting in poor
  # combinations.  NB however we don't list ALL elements in
  # mostElements (see code later).
  mostElements="a,blockquote,caption,center,cite,code,col,colgroup,html,iframe,pre,body,div,p,input,select,option,textarea,table,tr,td,th,h1,h2,h3,h4,h5,h6,font,basefont,small,big,span,ul,ol,li,i,em,s,strike,nobr,tt,samp,kbd,b,strong,dl,dt,dd,blink,button,address,dfn,form,marquee,fieldset,legend,listing,abbr,q,menu,dir,multicol,img,plaintext,xmp,label,sup,sub,u,var,acronym,object,embed,canvas,video".split(",")
  html5Elements = "article,aside,bdi,command,details,summary,figure,figcaption,footer,header,hgroup,main,mark,meter,nav,progress,section,date,time,del,ins,svg,output,thead,tbody".split(",") # (not sure about 'date' but it's used by some sites)
  rubyElements = "ruby,rt,rp,rb".split(",") # NOT counted in mostElements
  html5Elements += ['text','text > tspan'] # used within svg, sometimes for nothing more than effect (unfortunately there doesn't seem to be a way of ensuring the containing svg is displayed large enough, but truncation is better than having the text go underneath other elements)
  mostElements += html5Elements
  mostElements += ['location'] # site-specific hack for lib.cam.ac.uk

  css={} ; printOverride = {}
  webkitScreenOverride = {} ; geckoScreenOverride = {} ; msieScreenOverride = {}
  webkitGeckoScreenOverride = {} ; webkitMsieScreenOverride = {} ; geckoMsieScreenOverride = {}
  for e in mostElements+rubyElements:
    css[e]=defaultStyle.copy()
    printOverride[e] = {"color":"black","background":"white"}.copy()
    printOverride[e]["*font-size"] = "12pt" # TODO: option?
    geckoMsieScreenOverride[e] = {"*column-count":"1"} # not Webkit (PageUp/PageDown bug in Chrome57 etc)
  # but there are some exceptions:

  for e in rubyElements: del css[e]["*text-align"]

  if not pixelSize:
    # Size = unchanged, much-reduced layout changes.  But a LOT of "modern" sites assume they can stack elements (DIV, A, etc) with some transparency.  This can result in obscuring text if we have solid colour backgrounds.  But we don't want it completely transparent (unless we can confirm that's correct for a site-specific hack) as we probably won't be able to catch all UI elements as exceptions.
    for e in css.keys():
      if 'background' in css[e] and not e in ['html','body']: css[e]['background'] = colour["translucent_background_compromise"]
    # Also do this for Firefox's PDF viewer:
    css["div.pdfViewer div.page > div.canvasWrapper + div.textLayer"]={"opacity":"1"}

  del css['svg']['*font-size'] # doesn't make sense to override, as it's subject to the resize of the whole SVG (usually an enlargement)
  del printOverride['svg']['*font-size']
  for e in ['text','text > tspan']: # may help with SVG Lilypond output
    del css[e]["*font-size"],css[e]["*font-family"],css[e]["*font-weight"],css[e]["*font-variant"]
    del printOverride[e]["*font-size"]
  
  for k in list(css["img"].keys()):
    if k.startswith("background"): del css["img"][k] # e.g. WhatsApp emoji uses a single image with positioning (and we want this to work if size=unchanged)
  for k in list(printOverride["img"].keys()):
    if k.startswith("background"): del printOverride["img"][k]
  css["rt:lang(cmn-hans),rt:lang(zh)"]={"*font-family":pinyin_fonts}
  del css["rt"]["*padding"] # some sites omit space between ruby elements and make up for it by setting padding on the rt elements: let that through
  del css["ruby"]["*padding"];del css["rb"]["*padding"] # might as well do this too

  for w in ["*width","*height"]: del css["svg"][w] # 'auto' is very often wrong for svg, and some browsers' understanding of specificity results in our viewBox overrides not working if auto is set here

  for t in ["textarea","html","body","input"]:
    css[t]["*overflow"] = "auto"
  # 'html' is there for IE7.  But Firefox needs it to be 'visible'.  See hack at end.
  # TODO previously excluded 'body' (and deleted 'body' overflow 'visible')
  # as it somehow disables keyboard scrolling in IE7, however do need to
  # set 'body' to "auto' to work around CouchDB's "overflow:none" in both
  # 'html' and 'body' (at least in Firefox); need to find an IE7 to re-test
  # (if broken, consider re-instating the delete and move body:auto to the
  # non-IE7 override hack at end)
  # del css["body"]["*overflow"] # Do not set both "body" and "html" in IE7 - it disables keyboard-only scrolling!
  del css["input"]["*overflow"] # for IE 6 and possibly 8 overprinting too-long input type="text" with a horizontal scrollbar

  for e in [ # remove height:auto and width:auto from:
      "object","embed", # should not be forced to 'auto' as that can sometimes break Flash applications (when the Flash application is actually useful)
      "img", # can break on some versions of IE (is added back in for other browsers below)
      "input", # can result in 0 on some versions of Gecko (Firefox 60-62 are affected, at least with checkboxes and radio buttons)
      ]:
    del css[e]["*width"], css[e]["*height"]
  css[exclude_ie_below_9+"img"]={"*width":"auto","*height":"auto"} # but we can at least add img back on non-IE browsers (TODO: which versions of IE were affected?) - we DO need to specify this, to cope with sites that do silly things like set image height to something e+7 pixels and expect layering to compensate

  css["textarea"]["*width"]="100%" # not "auto", as that can cause Firefox to sometimes indent the textarea's contents off-screen

  css["frame"]={}
  for e in ["frame","iframe"]: css[e]["*overflow"]="auto" # to override 'scrolling=no' which can go wrong in large print (but this override doesn't always work)

  css["sup"]["*vertical-align"] = "super" # in case authors try to do it with font size instead
  css["sub"]["*vertical-align"] = "sub"

  css["marquee"]["*-moz-binding"]="none" # don't scroll marquee elements
  css["marquee"]["*display"]="block"

  css["center"]["*text-align"] = "center"
  
  for s in ['s','strike']: css[s]["*text-decoration"]="line-through"
  # TODO: not sure if really want this for the 's' alias of 'strike', since some sites e.g. http://www.elgin.free-online.co.uk/qp_intro.htm (2007-10) use CSS to override its presentation into something other than strikeout
  css['span[style="text-decoration:line-through"],span[style="text-decoration:line-through;"]']={"*text-decoration":"line-through"} # used on some sites

  # Margin exceptions:

  css["body"]["*margin"]="1ex %.1fpx 1ex %.1fpx" % (pixelSize*5/18.0,pixelSize*5/18.0) # keep away from window borders

  for i in "p,multicol,listing,plaintext,xmp,pre".split(","): css[i]["*margin"]="1em 0"
  css["li > p:first-child"]={"*margin-top":"0"} # I'm not sure P is intended to go inside LI like this (especially when there's only one paragraph), but GitHub does it as of 2017 so I suppose we should try to cope (positioning of the circle is still a bit sub-optimal though)
  
  listStuff="ul,dir,menu,dl,li".split(",") # not ol, leave that as margin 0px - see ol > li below
  for l in listStuff:
    css[l]["*margin"]="0 1em 0 %.1fpx" % (pixelSize*10/18.0)
  listStuff.remove("li")
  for l in listStuff:
    for l2 in listStuff:
      css[l+" "+l2]={"*margin":"0px"}
  css["ol > li"] = {"*list-style-position":"inside","*margin":"0px","*padding-left":"1em","*text-indent":"-1em"} # helps when numbers get very large
  css["blockquote"]["*margin"]="1em 4em"
  css["blockquote[type=cite]"]={"*margin":"1em 0px","*padding":"1em 0px 0px 0px"}
  css["dd"]["*margin"]="0em 2em"
  
  for t in ["th","td"]:
    css[t]["*padding"]="%.1fpx" % (pixelSize/18.0,)
    css[t+'[align^="right"]'] = {"*text-align":"right"}
  
  # Don't say white-space normal on user input elements or pre
  # Galeon 1.25: we also have to exclude "body" and "div" for some reason
  # TODO: is it REALLY a good idea to leave 'div' on this list?
  for e in "pre,input,textarea,body,div".split(","): del css[e]["*white-space"]
  for e in "font,code,tt,span,b".split(","): css["pre "+e]={"*white-space":"inherit"} # some mailing lists etc have "font" within "pre", and some sites have "code" within "pre"
  
  # Monospaced elements
  for t in "pre,code,tt,kbd,var".split(","): css[t]["*font-family"]="monospace"
  # and 'samp' let's have sans-serif
  for t in "samp".split(","): css[t]["*font-family"]=sans_serif_fonts
  
  css["spacer"]={"*display":"none"} # no point in keeping the spacers now we've changed the layout so much
  css["a"]["*display"] = "inline" # some sites override it to block, which might have worked OK in their CSS's context but it's not so good in ours

  # max-width (if supported, i.e. not IE6) can reduce left/right scrolling -
  # if one line's linebox needs to expand (e.g. due to a long word), then we
  # don't want to expand the whole block (e.g. the table cell) and all its
  # other line boxes.  BUT: if a max-width'd TD (or even a DIV etc) does
  # have to overflow in a big way (e.g. due to map images), and there is
  # something else to the right (e.g. nested tables with rowspans),
  # overprinting can result, unless also using 'overflow:auto' which can
  # create too many nested or offscreen scrollbars.  No way to say "use this
  # width for internal formatting, then expand to overflows for external
  # bounds" or "use this width if you are a leaf node with mostly text" or
  # whatever.  Only alternative for now is to say "none" and have to
  # horizontally scroll.  (Even "p" is not safe to set - consider a
  # table containing a p containing another table that overflows.)
  # (If set td max-width to "-moz-available" later in the stylesheet, will
  # cause Firefox 3 to do less overprinting than it would have done while
  # Firefox 2 takes the previous one and does a better job incorrectly, but
  # then there are still some instances of overprinting regardless of
  # version etc., especially on mapping sites)
  
  # (Note: On Firefox 2 (not 3), max-width works in a nice way, see Bugzilla
  # bug report at https://bugzilla.mozilla.org/show_bug.cgi?id=452840 - so
  # you may want to uncomment the following if you are particularly on Firefox 2.)
  
  # for e in mostElements: css[e]["*max-width"]=("%.1fpx" % min(1200,pixelSize*470/18))

  # Links stuff - must be before bold/italic colour overrides:
  for linkInside in ",font,big,small,basefont,br,b,i,u,em,cite,strong,abbr,span,div,code,tt,samp,kbd,var,acronym,h1,h2,h3,h4,h5,h6".split(",")+rubyElements:
    for lType in [":link",":visited","[onclick]",
                 ".button", # used by some JS applications
                 ]:
      css["a"+lType+" "+linkInside]={"color":colour["link"],"text-decoration":"underline","cursor":"pointer"}
      printOverride["a"+lType+" "+linkInside]={"color":"#000080"} # printing: links in blue might be useful for sending PDFs to others, but make it a dark blue so still readable if printed in black and white (don't try to ensure page is ALWAYS black and white: that can't be done w/out suppressing images.  User needs to suppress colour at print time.  But ensure legible choice of shading when that happens.)
      css["a"+lType+":hover "+linkInside]={"background":colour["hover-bkg"]}
      css["a"+lType+":active "+linkInside]={"color":"red","text-decoration":"underline","cursor":"pointer"}
      if linkInside in ["b","i","em","u","strong"] and not css[linkInside]["color"]==colour["text"]: css["a"+lType+" "+linkInside]["color"]=css[linkInside]["color"]
    css["a:visited "+linkInside]["color"]=colour["visited"]
  # set cursor:pointer for links and ANYTHING inside them (including images etc).  The above cursor:auto should theoretically do the right thing anyway, but it seems that some versions of Firefox need help.
  for linkInside in mostElements+rubyElements:
    for lType in [":link",":visited","[onclick]"]:
      key="a"+lType+" "+linkInside
      css.setdefault(key,{})["cursor"]="pointer"
      if not linkInside in rubyElements: css[key]["*display"]="inline" # some sites have 'div' or do JS things with 'span'...

  # Italic and bold:
  for i in "i,em,cite,address,dfn,u".split(","):
    css[i+" span"]={
      "*font-family":sans_serif_fonts,
      "color":colour["italic"]}
    printOverride[i+" span"]={"color":"black"}
    css[i].update(css[i+" span"])
  for i in "b,strong".split(","):
    css[i+" span,"+i+" kbd"]={
      "*font-weight":"bold",
      "color":colour["bold"]}
    printOverride[i+" span,"+i+" kbd"]={"color":"black"}
    css[i].update(css[i+" span,"+i+" kbd"])
  css["acronym"]["color"]=colour["bold"]
  css["abbr"]["color"]=colour["bold"]
  css["ins"]["color"]=colour["italic"]
  css["del"]["color"]=colour["italic"]
  css["del"]["text-decoration"]="line-through"
  # Some browsers might start styling abbr by default but not acronym.  Some older browsers might understand acronym title= but not abbr title=, so some sites might try to use acronym= for backward compatibility, but given that this must be for nonessential information anyway (as many simpler browsers don't support either) it probably makes sense to prefer abbr now (if it might be displayed by default on a greater number of modern browsers) unless the webmaster wants to emulate the browser in CSS.
  css["acronym"]["border-bottom"]="1px dotted"
  css["abbr"]["border-bottom"]="1px dotted"

  # Headings stuff (must be after italic/bold):
  indent = 0
  for h in range(6):
    el="h%d" % (h+1)
    css[el]["*font-family"]=sans_serif_fonts
    size = (largestHeadingSize-h*(largestHeadingSize-smallestHeadingSize)/(6-1.0))
    css[el]["*font-size"]="%.1fpx" % size
    css[el]["*font-weight"]="bold"
    # ensure 'h1 strong' etc inherits family (but not necessarily colour):
    for i in ['strong','em','i','b']:
      css[el+" "+i]=css[el].copy()
      css[el+" "+i]["color"]=css[i]["color"]
      printOverride[el+" "+i]={"color":"black"}
    # now for heading colour:
    css[el]["color"]=colour["headings"]
    printOverride[el]={"color":"black"}
    # ensure links in headings inherit size and family:
    css[el+" center"]=css[el].copy() # rather than the default for 'center'
    css[el+" a"]=css[el].copy() # because it's usually A NAME (in the case of HREF, the specificity of a:link should be greater)
    css[el+" abbr"]=css[el].copy() ; del css[el+" abbr"]["*text-decoration"]
    css[el+" span"]=css[el].copy()
    css[el+" a b"]=css[el].copy()
    printOverride[el+" center"]=printOverride[el].copy()
    printOverride[el+" a"]=printOverride[el].copy()
    printOverride[el+" abbr"]=printOverride[el].copy()
    printOverride[el+" span"]=printOverride[el].copy()
    printOverride[el+" a b"]=printOverride[el].copy()
    # and now (AFTER the above) set margins on headings
    if h: indent += size
    css[el]["*margin"]="0px 0px 0px %.1fpx" % indent

  # Images and buttons:
  css["img:not(.emoji)"]={"background":colour["image_transparency_compromise"]} # see WhatsApp exception above
  
  # Exception needed for MediaWiki TeX images
  # (they tend to be transparent but with antialiasing that
  # assumes the background will be white)
  css["body.mediawiki img.tex"]={"background":"white"}
  # (note however it might be possible to set the wiki to
  # display maths as real TeX or something instead)
  if not colour["background"]=="white": css["body.mediawiki img.tex"]["border"]="white solid 3px" # to make sure letters near the edge are readable if the rest of the page has a dark background
  
  if "image_opacity" in colour.keys():
    del css["img"]["*opacity"],css["img"]["filter"]
    css["img"]["opacity"]="%g" % colour["image_opacity"]
    css["img"]["filter"]="alpha(opacity=%d)" % int(colour["image_opacity"]*100) # for IE8 and below
    if colour["image_opacity"]<0.9: css["img:hover"] = css["a:hover img"]={"opacity":"0.9","filter":"alpha(opacity=90)"}
  
  css["button"]["background"]=colour["button-bkg"]
  printButtonBackground = "#e0e0e0" # light grey, TODO: option
  printOverride["button"]["background"]=printButtonBackground
  css['div[role="button"]']={"background":colour["button-bkg"]} # for Gmail 2012-07 on "standard" view (rather than "basic HTML" view).  "Standard" view might work for people who want the "unchanged" size.
  printOverride['div[role="button"]']={"background":printButtonBackground}
  if "alt-backgrounds" in colour.keys():
    # override specificity of alt-backgrounds div:nth-child
    css['html body div[role="button"]'] = css['div[role="button"]']
    printOverride['html body div[role="button"]'] = {"background":printButtonBackground}
  css["input[type=submit]"]={"background":colour["button-bkg"]}
  css["input[type=button]"]={"background":colour["button-bkg"]}
  css["input[type=reset]"]={"background":colour["reset-bkg"]}
  printOverride["input[type=submit]"]={"background":printButtonBackground}
  printOverride["input[type=button]"]={"background":printButtonBackground}
  printOverride["input[type=reset]"]={"background":printButtonBackground}
  for f in ["select","input","textarea","button"]:
    k = "html "+f+'[disabled]' # must include 'html' so more specific than above (TODO: or :not(:empty) if got enough CSS?)
    if f=='input': k += ", html "+f+'[readonly]'
    css[k]={"background":colour["form_disabled"]}
    printOverride[k]={"background":printButtonBackground} # TODO: or something else?
  
  # Separate adjacent links (CSS2+)
  if (pixelSize and separate_adjacent_links_at_other_sizes) or (not pixelSize and separate_adjacent_links_at_size_0):
    for l in [":link",":visited","[onclick]"]:
      css[exclude_ie_below_9+"a"+l+":before"]={"content":'"["',"color":colour["text"],"text-decoration":"none","white-space":"nowrap"}
      css[exclude_ie_below_9+"a"+l+":after"]={"content":'"]"',"color":colour["text"],"text-decoration":"none","white-space":"nowrap"}
      # make sure the hover colour includes :before and :after - this is needed if the :before/:after text is changed by site-specific hacks etc (to cope with empty links)
      css[exclude_ie_below_9+"a"+l+":hover:before"]={"background":colour["hover-bkg"]}
      css[exclude_ie_below_9+"a"+l+":hover:after"]={"background":colour["hover-bkg"]}
      printOverride[exclude_ie_below_9+"a"+l+":before"]={"color":"black"} # TODO: option to delete the "[" "]" content also?
      printOverride[exclude_ie_below_9+"a"+l+":after"]={"color":"black"}
      
  # Avoid style overrides from :first-letter, :first-line,
  # :before and :after in author's CSS.  However be careful
  # which elements you do this because of browser bugs.
  firstLetterBugs_multiple=[
  "input","select","option","textarea","table","colgroup","col","img", # probably best to avoid these
   "div", # Gecko messes up textarea when enter multiple paragraphs; Safari has text selection visibility problem see below
   "svg","text","text > tspan","object", # doesn't make sense, and can cause confusion
  ]
  firstLetterBugs_geckoOnly=[
    # none here for now
  ]
  firstLetterBugs_webkitOnly=[
  # The following cause text selection visibility problems in Webkit / Safari 5/6 (cannot be worked around with :first-letter::selection)
  # (added 'caption' 2022: causing selection issues in Safari 15)
  # (+ Chrome 12 bug - OL/LI:first-letter ends up being default size rather than css size; harmless if have default size set similarly anyway)
    "main", # Safari 17.3
    "label","address","p","ol","ul","li","pre","code","body","html","h1","h2","h3","h4","h5","h6","form","th","tr","td","dl","dt","dd","b","blockquote","section","header","footer","center","article","span","aside","figure","caption","figcaption","time","em"
  ]
  firstLetterBugs_msie=["a"]
  assert not(any([(x in firstLetterBugs_geckoOnly or x in firstLetterBugs_webkitOnly or x in firstLetterBugs_msie) for x in firstLetterBugs_multiple]) or any([(x in firstLetterBugs_webkitOnly or x in firstLetterBugs_msie) for x in firstLetterBugs_geckoOnly]) or any([(x in firstLetterBugs_msie) for x in firstLetterBugs_webkitOnly])), "Error: firstLetterBugs item in more than one category"
  firstLineBugs=[
  "div", # on firefox 2 causes some google iframes to occlude page content
  "svg","text","text > tspan","object", # doesn't make sense, and can cause confusion
  "input","select","option","textarea","table","colgroup","col","img",
  "td","th", # causes problems on Firefox 2 if there's a form inside
  "a", # causes problems in IE
  "span", # sometimes causes crashes in Opera 12
  "li", # sometimes causes crashes in Opera 12 (note this might be sacrificing some control, if someone does try a li:first-line override)
  # To be safe, could add other inline-etc tags mentioned in mostElements:
  "label","nobr","tr","ol","ul","abbr","acronym","dfn","em","strong","code","samp","kbd","var","b","i","u","small","s","big","strike","tt","font","cite","q","sub","sup","blink","button","command","dir","embed","object","fieldset","iframe","marquee","basefont","bdi","canvas","time",
  # TODO: other :first-line, :first-letter and :hover overrides can still crash Opera 12 on some sites.  Have suggested in index.html that the user replaces :first with :girst and :hover with :gover when installing one of these CSS files to Opera.
  ]
  inheritDic={"color":"inherit","background":"inherit","*letter-spacing":"inherit","*font-size":"inherit","*font-family":"inherit"}
  # (NB must say inherit, because consider things like p:first-line / A HREF... - the first-line may have higher specificity.
  # If IE7 seems to be getting first lines and first letters wrong, check that Ignore Document Colours is NOT set - "document" can include parts of the CSS.  and try toggling high-contrast mode twice.)
  for e in mostElements:
    if not e in firstLetterBugs_multiple:
      if e in firstLetterBugs_geckoOnly: dictToAddTo = webkitScreenOverride # or webkitMsieScreenOverride, but would have to test MSIE versions
      elif e in firstLetterBugs_webkitOnly: dictToAddTo = geckoScreenOverride # or geckoMsieScreenOverride, but would have to test MSIE versions
      elif e in firstLetterBugs_msie: dictToAddTo = webkitGeckoScreenOverride
      else: dictToAddTo = css
      dictToAddTo[e+":first-letter"]=inheritDic.copy()
    if not e in firstLineBugs: css[e+":first-line"]=inheritDic.copy()
    for i in map(lambda x,e=e:exclude_ie_below_9+e+x,[":before",":after"]):
      css[i]=defaultStyle.copy()
      if e=="img": del css[i]["background"]
      else: css[i]["background"]="transparent" # essential for 0.css where the pseudo-element might be repositioned with different z-index; not supported by IE below 9 but neither are pseudo-elements in general (we're on exclude_ie_below_9 anyway)
      for mp in ["*margin","*padding"]:
        if not css.get(e,{}).get(mp,"")==css[i][mp]:
          del css[i][mp] # as not sure how browsers would treat a different margin/padding in :before/:after.  But DO keep these settings for the 0px elements, because we DON'T want sites overriding this and causing overprinting.
  # and also do this for no specific element:
  for i in map(lambda x:exclude_ie_below_9+x,[":before",":after"]):
    css[i]=defaultStyle.copy() # (especially margin and padding)
    css[i]["background"]="transparent" # see above
  # inheritDic may also be useful for common child elements of links, highlights etc:
  for e in rubyElements:
    css[e].update(inheritDic)
    del printOverride[e]

  # CSS 2+ markup for viewing XML+CSS pages that don't use HTML.  Not perfect but should be better than nothing.
  xmlKey=":root:not(HTML):not(page):not(svg), :root:not(HTML):not(page):not(svg) :not(:empty)"
  # Careful not to use the universal selector, because it can mess up Mozilla's UI.
  # :not(page) is an important addition for recent versions of Firefox whose Preference pages start with 'page' (can be rendered invisible if apply whole of defaultStyle to it).
  css["page:root *"]={"background-color":colour["background"]} # to normalise recent-Firefox preferences pages (without this, some parts do and some don't; result can look too stark).  Tested in Firefox 45.4.
  css[xmlKey]=defaultStyle.copy()
  del css[xmlKey]["*text-decoration"] # because this CSS won't be able to put it back in for links (since it doesn't know which elements ARE links in arbitrary XML)
  # Exception to above for Mozilla scrollbars:
  css[":root:not(HTML):not(page):not(svg) slider:not(:empty)"]={"background":"#301090"}
  # and Firefox icons: (TODO: this may need re-testing on affected versions of Firefox; needed to add :not(svg) or get link-coloured parts in object-embedded SVG files in Safari)
  css[":root:not(HTML):not(svg) *"]={"-moz-context-properties":"fill,fill-opacity","fill":colour["link"],"fill-opacity":"1"}

  checkbox_scale = int(pixelSize/16)
  for iType in ["checkbox","radio"]:
    iKey = "input[type="+iType+"]"
    if checkbox_scale > 1: css[iKey]={"transform":"scale(%d,%d)" % (checkbox_scale,checkbox_scale),"margin":"%dpx"%(checkbox_scale*6)} # margin not padding (browser problems)
    else: css[iKey]={}
    css[iKey]['-webkit-appearance']=iType
    if not pixelSize: css[iKey]['width']=css[iKey]['height']='auto' # (this override shouldn't be needed if non-unchanged sizes have overridden it anyway, but override even at size=unchanged in case sites use width=height=0 to hide these controls and use image-only versions that don't work in our colour scheme)
    if browser_is_Firefox_73: css[iKey]['-webkit-appearance'] += ' !important; -moz-appearance: none'
    if not pixelSize: css[iKey]['opacity']='100%'
  if pixelSize:
    # In many versions of firefox, a <P ALIGN=center> with an <IFRAME> inside it will result in the iframe being positioned over the top of the main text if the P's text-align is overridden to "left".  But missing out text-align could allow websites to do full justification.  However it seems OK if we override iframe's display to "block" (this may make some layouts slightly less brief, but iframes usually need a line of their own anyway)
    css["iframe"]["*display"]="block"
    # and if we're doing that, we might as well use the full width:
    css["iframe"]["*width"]="100%"
    # The following may help a little as well: make iframes 50% transparent so at least we can see what's under them if they do overprint (depends on the browser and the site; apparently the IFRAME's height can be treated as close to 0 when it's not) (fixed? keeping this anyway just in case)
    css["iframe"].update({"*filter":"alpha(opacity=50)","*opacity":"0.5"})

  # float exceptions for img align=left and align=right (might as well)
  css["img[align=left]"]={"*float":"left"}
  css["img[align=right]"]={"*float":"right"}
    
  # Selection (CSS3)
  if "selection-bkg" in colour.keys():
    css["::selection"] = {"background":colour["selection-bkg"]}
    css["::-moz-selection"] = {"background":colour["selection-bkg"]}

  css['input[type=search]'] = {
    "-webkit-appearance":"textfield", # searchbox forces background:white which may conflict with our foreground
    }
  css['input[type=search]']['-webkit-appearance'] += ' !important; -moz-appearance: none' # needed on both Firefox 73 and 86.  In Firefox 86 with -moz-appearance and -webkit-appearance textfield, specifying border-width 1px somehow makes all type=search fields white.  Not specifying border-width (but setting a border-radius) will still leave some type=search turning white, even when it's unclear the site itself is setting borders, so more must be at play here.  Setting appearance to none makes none of them white, even when border-width is set, and even when border-radius is not set.  -moz-appearance overrides -webkit-appearance only if specified after it.
  
  css['select']['-webkit-appearance']='listbox' # workaround for Midori Ubuntu bug 1024783
  css['select']['-webkit-appearance'] += ' !important; -moz-appearance: none' # even if not browser_is_Firefox_73
  css['select']['background']=colour["select-bkg"]
  printOverride['select']['background']=printButtonBackground # TODO: or something else?

  if "alt-backgrounds" in colour.keys():
    css['td:nth-child(odd),div:nth-child(odd)'] = {"background":colour["alt-backgrounds"][0]}
    printOverride['td:nth-child(odd),div:nth-child(odd)'] = {"background":"white"} # TODO: or a very light grey?
    if len(colour["alt-backgrounds"])>1:
      css['td:nth-child(even),div:nth-child(even)'] = {"background":colour["alt-backgrounds"][1]}
      printOverride['td:nth-child(even),div:nth-child(even)'] = {"background":"white"} # TODO: or another very light grey?
    for k in list(css.keys()):
      if css[k].get("background","")==colour["background"] and not k in ["html","body"]: css[k]["background"]="inherit"

  # Make definition lists a bit more legible, including when there is more than one definition for one term
  css['dd+dd']={'*padding-top':'0.5ex','*margin-top':'1ex','*border-top':'thin dotted grey'}
  css['dt'].update({'*padding':'0.5ex 0px 0px 0px','*margin':'1ex 0px 0px 0px','border-top':'thin grey solid'})
  
  css['hr']={"color":"grey","border-style":"inset"} # prevent pages from changing the colour of horizontal rules, especially to black if we have a black background (sometimes used within tables to mimic fraction lines in formulae)
  for aside in ['aside','figure']: css[aside]['border']="thin "+colour["italic"]+" solid" # might help sometimes
  css['body > pre:only-child']={'*white-space':'pre-line','*font-family':serif_fonts} # this might make Gopher pages easier to read in Firefox's "OverbiteFF" (unless ASCII art is in use); NB on some firefox versions it slows down the loading of text/plain URLs and chrome://browser/skin/browser.css etc
  css['body > form[action="man:"] + pre']={'*white-space':'pre-line','*font-family':serif_fonts} # ditto for Bwana manpage-viewing plugin for Mac OS X browsers
  
  for pt in '::-webkit-input-placeholder,:-moz-placeholder,::-moz-placeholder,:ms-input-placeholder,::placeholder,:placeholder-shown'.split(","): css[pt] = {"color":colour["form_disabled"]}

  # Don't blur GIFs and PNGs if showing images in high DPI
  css['img[src$=".gif"], img[src$=".png"]'] = { 'image-rendering':'crisp-edges','-ms-interpolation-mode':'nearest-neighbor' }

  css['main']['*max-width']='100%' # work around too wide on some sites
  css['input']['*max-width']='100%'
  css['select']['*max-width']='100%'
  css['details']['border-left']=colour["form_disabled"]+" solid"
  css['details > summary']={'background':colour["button-bkg"]}

  # SVG (including Firefox controls etc)
  css["svg div,svg rect,svg circle,svg line,svg polyline,svg polygon,svg path,svg ellipse"]={"background":"transparent","fill":"transparent"}
  css['svg rect[fill="currentColor"],svg circle[fill="currentColor"],svg polygon[fill="currentColor"],svg path[fill="currentColor"],svg ellipse[fill="currentColor"]']={"fill":colour["text"]}
  css["svg rect[stroke],svg circle[stroke],svg line,svg polyline,svg polygon[stroke],svg path,svg ellipse[stroke]"]={"stroke":colour["text"],"stroke-width":"1px","vector-effect":"non-scaling-stroke"}
  css["svg:root"]={"background":colour["background"]}

  # Firefox about:config
  if not preapply_FfxDarkModeExceptions:
    css['table#prefs button.button-toggle:empty:before']={'content':r'"\23FC"'}
    css['table#prefs button.button-reset:empty:before']={'content':r'"\23FB"'}
    css['table#prefs button.button-edit:empty:before']={'content':r'"\270E"'}
    css['table#prefs button.button-add:empty:before']={'content':r'"+"'}
  
  # Begin site-specific hacks

  if not pixelSize: css['div.icon:not(:empty)']={
      # This might contain text for speech that's hidden from graphical browsers, but we want to show it anyway because the graphical icon probably won't show
      "height":"auto","width":"auto","text-indent":"0px"} # not -1000px or whatever they did to put the text off-screen

  def emptyLink(lType,content,css,printOverride,colour,isRealLink=True,omitEmpty=False,isInsideRealLink=False,undo=False,unchangedSizeOnly=False):
   assert not ',' in lType
   assert not (undo and content)
   if isInsideRealLink: isRealLink = False # overrides
   if omitEmpty: eList = [""]
   else: eList = [":empty",":blank",":-moz-only-whitespace"]
   if unchangedSizeOnly: prefix="**"
   else: prefix=""
   for empty in eList:
    # Fill in the text of an empty link according to
    # context (making up for the fact that we're not
    # displaying whatever CSS-oriented graphical thing
    # the site is showing).  lType is the link in context
    # and 'content' is our guess of what it should say.
    if isRealLink: key = lType+":link"+empty
    else: key = lType+empty
    if undo: css[key+":before"],css[key+":after"]={},{}
    else: css[key+":after"]={prefix+"color":colour["link"]} # (better make sure the colour is right, as it might be in the middle of a load of other stuff)
    if content:
      if isInsideRealLink: css[key+":after"][prefix+"content"]='"'+content+'"'
      else: css[key+":after"][prefix+"content"]='"'+content+']"' # overriding "]"
    elif not isInsideRealLink:
      if undo: css[key+":after"][prefix+"content"]='""'
      else: css[key+":after"][prefix+"content"]='"]"'
    if not undo:
      printOverride[key+":after"]={prefix+"color":"#000080"}
      css[key+":before"]={prefix+"color":colour["link"]}
      printOverride[key+":before"]={prefix+"color":"#000080"}
    if isRealLink:
      key = key.replace(":link",":visited")
      if not undo:
        css[key+":after"]={prefix+"color":colour["visited"]}
        printOverride[key+":after"]={prefix+"color":"#000080"}
        css[key+":before"]={prefix+"color":colour["visited"]}
        printOverride[key+":before"]={prefix+"color":"#000080"}
    else: # not isRealLink
      if not isInsideRealLink:
        if undo: css[key+":before"][prefix+"content"] = '""'
        else: css[key+":before"][prefix+"content"] = '"["'
      if undo: css[key]={prefix+"text-decoration":"none",prefix+"cursor":"auto",prefix+"color":colour["text"]}
      else:
        css[key]={prefix+"text-decoration":"underline",prefix+"cursor":"pointer",prefix+"display":"inline",prefix+"margin":"0px 1ex 0px 1ex",prefix+"color":colour["link"]}
        css[key+":before"][prefix+"cursor"] = css[key+":after"][prefix+"cursor"] = "pointer"
      for ll in ["",":before",":after"]:
        if undo: css[exclude_ie_below_9+key+":hover"+ll]={prefix+"background":"transparent"}
        else: css[exclude_ie_below_9+key+":hover"+ll]={prefix+"background":colour["hover-bkg"]}
      printOverride[key] = {prefix+"color":"#000080"}

  css["div.standardModal-content > div.itemImage:first-child > img"]={"*display":"none"} # 'logo bigger than browser' syndrome

  # Hack for Google search results:
  css['body#gsr.srp a[href] > h3']={"**z-index":"1"}
  css["g-img"]={"*display":"inline","*position":"static"}
  css["g-inner-card"]={"background":colour["background"]}
  css["span.vshid"]={"*display":"inline"} # TODO: rm * ?
  css['img[src^="/images/nav_logo"][alt="Google"]']={"*display":"none"}
  css['div.gb_tc.gb_uc.gb_Vb:empty,div.gb_uc.gb_vc.gb_Wb:empty,span.gb_0a:empty']={"*display":"none"} # TODO: if gb = Great Britain then we might need to rewrite this to cover other countries.  The div has a :before rule with image content, takes up lots of screen space and is not functional. (2016-10)
  css['div.sbibtd > div#sfdiv.sbibod > button.sbico-c > span.sbico._wtf._Qtf']={"*display":"none"}
  css['table.gssb_c[style~="absolute;"]']={"*position":"absolute"}
  for leaf in ['td','span','a','b']: css['table.gssb_c tr.gssb_i '+leaf]={"background":colour["highlight-bkg"]} # TODO: be more specific by saying gssb_c[style~="absolute;"] again ?
  css['div.sbtc div.sbsb_a li.sbsb_d div']={"background":colour["highlight-bkg"]} # suggestions cursor 2015-04
  css['a#logo > img[src="/images/nav_logo195.png"]']={"*display":"none"}
  css['div#main div#cnt div#rcnt div.col div#ifb div.rg_meta,div#main div#cnt div#rcnt div.col div#ifb div.rg_bb_i div.rg_bb_i_meta']={"*display":"none"} # image search
  css['div#mngb > div#gb > div.gb_Sb,body#gsr.srp > div#mngb']={"*display":"none"} # other graphical clutter they added 2014-09 and 2014-10
  css['div#gbqfbw > button#gbqfb > span.gbqfi:empty']={'*display':'none'} # 2549-pixel high image on Android shop that messes up scrolling 2016-08
  css['div.kv > cite + div.action-menu.ab_ctl > a[aria-label="Result details"]'] = {'*display':'none'} # it's supposed to just reveal the "Cached" or "Similar" options, but these should be displayed anyway with our CSS so it's a non-functional unlabelled link: save confusion
  # Hack for Wikipedia/MediaWiki diffs (diffchange) and Assembla diffs (was, now) and Sourceforge (vc_, gd, gi, .diff-*) and GitHub (code-deletion, code-addition, diff-line-row) and CGit
  k = ".diffchange, .was, .now, .vc_diff_change, .vc_diff_remove, .vc_diff_add, .wDiffHtmlDelete, .wDiffHtmlInsert, pre > span.gd, pre > span.gi, .diff-chg, .diff-add, .diff-rem, table.diff-table td.blob-code-deletion span, table.diff-table td.blob-code-addition span, tr.diff-line-row code.deletion span, tr.diff-line-row code.addition span, body > div.cgit .diff .del, body > div.cgit .diff .add"
  css[k] = {"color":colour["italic"]}
  printOverride[k] = {"color":"black"} # TODO: shade of grey?
  css[".wDiffHtmlDelete"]={"*text-decoration":"line-through"}
  css['button[aria-label="Add line comment"] > svg.octicon-plus']={"display":"none"} ; emptyLink('table.diff-table button[aria-label="Add line comment"]','C',css,printOverride,colour,False,True) # GitLab: making those buttons look like "+" just to the left of the diff's "-" and "+" is confusing
  css['svg[aria-label="status_success"]'],css['svg[aria-label="status_failed"]'] = {'border':'green solid'}, {'border':'red solid'} # GitLab pipelines
  css['div.web-ide-promo-popover']={'**display':'none'} # GitLab 2024: sorry but when a screen magnifier is in use, the effective window size is much smaller than what your designers imagined, and that non-dismissable IDE promotion actually blocks us from using your entire site, so let's remove it (at size=unchanged; at other sizes the layout is changed anyway)
  css['button.more-actions-toggle > span.icon > svg']={'width':'1em','height':'1em'}
  # and media players:
  css["div.mwPlayerContainer div.play-btn span.ui-icon-play:empty:after"]={"content":r'"\21E8 Play"'}
  css["div.mwPlayerContainer div.play-btn span.ui-icon-pause:empty:after"]={"content":'"Pause"'}
  css['body.mediawiki div[title="Play clip"]:empty:after']={"content":'"Play clip"'}
  # Hack for jqMath:
  if pixelSize: css["td.fm-num-frac,td.fm-den-frac"] = {"text-align":"center"}
  # Partial hack for MathJax:  (I wish webmasters would use
  # jqMath, which is easier on user CSS, instead)
  # NB we use div.MathJax_Display here but it's expanded to inline MathJax in outCss
  if pixelSize:
    css["div.MathJax_Display span.mfrac,span.MathJax span.mfrac"]={"display":"inline-table","vertical-align":"middle","padding":"0.5ex"}
    css["div.MathJax_Display span.mfrac > span > span,span.MathJax span.mfrac > span > span"]={"display":"table-row-group","text-align":"center"}
    css["div.MathJax_Display span.mfrac > span > span:first-child,span.MathJax span.mfrac > span > span:first-child"]={"display":"table-cell","border-bottom":"thin solid"}
    css["div.MathJax_Display span.mfrac > span > span + span + span,span.MathJax span.mfrac > span > span + span + span"]={"display":"none"}
    css["div.MathJax_Display span.msqrt > span > span + span,span.MathJax span.msqrt > span > span + span"] = {"display":"none"}
    css["div.MathJax_Display span.msqrt:before,span.MathJax span.msqrt:before"]={"content":r'"\221A("'}
    css["div.MathJax_Display span.msqrt:after,span.MathJax span.msqrt:after"]={"content":'")"'}
    css["div.MathJax_Display span.mtable,span.MathJax span.mtable"]={"display":"inline-table"}
    css["div.MathJax_Display span.mtable span.mtd,span.MathJax span.mtable span.mtd"]={"display":"table-row-group","text-align":"center"}
    for el in [""," span"," img:after"]: css["div.MathJax_Display span.msubsup > span:only-child > span:first-child + span:last-child"+el]={"color":colour["italic"]} # for now, because we don't know if the span:last-child's "vertical-align" should be "sub" or "super" in this context
    css["div.MathJax_Display span.msubsup > span:only-child > span:first-child + span:not(:last-child)"]={"vertical-align":"super"} # TODO: can we do superscript + subscript as an inline-table? (but need a containing element?)
    css["div.MathJax_Display span.msubsup > span:only-child > span:first-child + span + span"]={"vertical-align":"sub"}
  # Following workaround is for MathJax scripts which insist on images when we have fonts (TODO: check for Unicode support?)  It doesn't work in IE9 or below (and possibly some other browsers) because it relies on setting img's content="" to enable the :before/:after; to be safe I'm doing this in only Webkit and Gecko for now.
  for asc in list(range(0x20,0x7f))+[0xa0,0xd7]+list(range(0x2200,0x2294)): # TODO: others?
    if asc in [ord('"'),ord('\\')]: continue
    k = 'div.MathJax_Display img[src="http://cdn.mathjax.org/mathjax/latest/fonts/HTML-CSS/TeX/png/Main/Regular/476/%04X.png"]' % asc
    webkitGeckoScreenOverride[k]={"width":"0px",'content':'""',"vertical-align":"0px"} # (don't say display=none or that'll hide the :after as well)
    if asc <= 0x7f: c = chr(asc)
    else: c = r'\%04X' % asc
    webkitGeckoScreenOverride[k+":after"]={"content":'"'+c+'"'}
  # Hack for unedited links on WP/MediaWiki and other wikis:
  css["a:link.new, a:link.new i,a:link.new b, div#main-content #main-entry div#main-article a:link.createlink"]={"color":colour["coloured"] } # (TODO use a different colour?)
  printOverride["a:link.new, a:link.new i,a:link.new b, div#main-content #main-entry div#main-article a:link.createlink"]={"color":"black" } # TODO: shade of grey?
  # and the navpopup extension: (also adding ul.ui-autocomplete to this, used on some sites)
  css['body.mediawiki > div.navpopup,body.mediawiki .referencetooltip,body.mediawiki .rt-tooltip, ul.ui-autocomplete, body.mediawiki div.mwe-popups']={"*position":"absolute","border":"blue solid","**background":colour["background"]}
  css["body.mediawiki > div.ui-dialog"]={"*position":"relative","border":"blue solid"} # some media 'popups'
  css["body.mediawiki div.mwe-popups a.mwe-popups-extract"]={"text-decoration":"none","color":colour["text"]} # don't underline if they present it as a very long link
  css["body.mediawiki div.mwe-popups-container footer"]={"display":"none"} # 2021-02: this popup footer doesn't show on our colour schemes anyway, and it's a setting to disable the popups taking screen space away from them, bad in large print
  # and the map pins (TODO: this is still only approximate! pins tend to be a bit too far to the south-west; not sure why) :
  css['body.mediawiki table tr div[style^="position:absolute"]']={"*position":"absolute","background-color":"transparent"}
  css['body.mediawiki table tr div[style^="position:relative"]']={"*position":"relative","*display":"inline-block","**background":colour["background"]} # inline-block needed because the percentage positioning of the 'absolute' pin div depends on the map div's width being set to that of the map (done on-site by hard-coding, but we would have to special-case it for every possible map width; inline-block is a workaround)
  css['body.mediawiki table tr div[style^="position:absolute"] div[style^="position:absolute"] + div']={"display":"none"} # or the place name would overprint the map too much; it can usually be inferred from the caption
  css["body.mediawiki a.cn-full-banner-click"]={"*display":"none"} # sorry, it was too big
  css['body.mediawiki div.chess-board > div[style^="position:absolute"]']={"*position":"absolute","**background":colour["background"]}
  css['body.mediawiki div.chess-board > div > a.image:before, body.mediawiki div.chess-board > div > a.image:after']={"content":'""'} # overriding our [..]
  css['a:link div']["*padding"]="0px" # WikiMedia some site notices (the div is set to display inline, and adding padding to inline elements can cause overprinting)
  css['body.mediawiki div#mw-navigation > div#mw-panel']={'**height':'100%','**overflow-y':'auto'} # for Wikimedia at size=unchanged: otherwise, when zoomed in, may get trouble with 2 scrollbars 2020-09 (because body is fixed at height 100% but excludes mw-panel, and bottom border of body is not clear so situation is difficult to distinguish from that of a rendering-as-blank EU cookie-consent popup obscuring much of the page)
  css['body.mediawiki div#vector-page-titlebar-toc']={'**display':'none'} # it gets in the way of the text on small windows
  
  # Syntax highlighting of code on various platforms:
  shl_keyword = {"color":colour["italic"]}
  shl_varname = {"color":colour["bold"]}
  shl_comment = {"color":colour["italic"],"opacity":"0.7"}
  shl_preproc = {"color":colour["headings"]}
  shl_string = {"background":colour["highlight-bkg"]}
  css['body.mediawiki .mw-highlight .k'] = shl_keyword # keyword
  css['pre > code > span.kwd'] = shl_keyword # StackOverflow keyword
  css['body.mediawiki .mw-highlight .kt'] = shl_keyword # keyword type
  css['body.mediawiki .mw-highlight .n']=shl_varname # (variable) name
  css['pre > code > span.pln'] = shl_varname # StackOverflow name
  css['body.mediawiki .mw-highlight .nf']=shl_varname # function name
  css['body.mediawiki .mw-highlight .nt']=shl_keyword # tag name(?) (in XML etc)
  css['body.mediawiki .mw-highlight .na']=shl_varname # attribute name
  css['body.mediawiki .mw-highlight .nb']=shl_keyword # bool
  css['body.mediawiki .mw-highlight .cm,body.mediawiki .mw-highlight .c1,body.mediawiki .mw-highlight .c']=shl_comment # comment
  css['pre > code > span.com'] = shl_comment # StackOverflow comment
  css['body.mediawiki .mw-highlight .cp']=shl_preproc # preprocessor
  css['body.mediawiki .mw-highlight .s']=shl_string # string
  css['body.mediawiki .mw-highlight .sd']=shl_string # multiline string etc
  css['pre > code > span.str'] = shl_string # StackOverflow string
  css['body.mediawiki .mw-highlight .se']={"background":colour["highlight-bkg"],"color":colour["bold"]} # string escape character
  css['body.mediawiki .mw-highlight .cpf']=shl_string # #include parameter (treated like string in some editors)
  css['body.mediawiki .mw-highlight .lineno']={"color":colour["form_disabled"]}
  css['a.disabled > span.buttonText']={"color":colour["form_disabled"]}
  # TODO: p = punc, o = operator; mi = integer; nv = variable name; nb; others?
  css['div.highlight > pre span.c1']=shl_comment # tornadoweb etc
  css['div.highlight > pre span.kn,div.highlight > pre span.k']=shl_keyword
  css['div.highlight > pre span.n,div.highlight > pre span.nn']=shl_varname
  css['div.highlight > pre span.s1,div.highlight > pre span.s2,div.highlight > pre span.sd,div.highlight > pre span.si']=shl_string
  # TODO: p = punc (and do we differentiate sd=docstring, si=% formatter)
  css['pre span.hljs-keyword'] = shl_keyword
  css['pre span.hljs-built_in'] = shl_varname
  css['pre span.hljs-string'] = shl_string
  css['pre span.hljs-comment'] = shl_comment
  css['pre span.hljs-number'] = shl_preproc
  css['pre span.hljs-meta'] = shl_preproc
  css['pre.code > span.com'] = shl_comment
  css['pre.code > span.str'] = shl_string
  css['pre.code > span.kwd'] = shl_keyword
  css['pre.code > span.pln'] = shl_varname
  css['pre > code span.c'] = shl_comment # GitLab issue tracker 2018-10
  css['pre > code span.c1'] = shl_comment
  css['pre > code span.s'] = shl_string
  css['pre > code span.s2'] = shl_string
  css['pre > code span.k'] = shl_keyword
  css['pre > code span.n'] = shl_varname
  css['pre > code span.na'] = shl_varname
  css['pre > code span.syntax-keyword'] = shl_keyword # XCode docs
  css['pre > code span.syntax-string'] = shl_string
  css['pre > code span.syntax-comment'] = shl_comment
  css['pre > code span.syntax-title'] = shl_varname
  css['pre > code span.syntax-built_in'] = shl_varname
  css['div.dp-highlighter > ol span.comment'] = shl_comment
  css['div.dp-highlighter > ol span.string'] = shl_string
  css['div.dp-highlighter > ol span.keyword'] = shl_keyword
  css['div.dp-highlighter > ol span.special'] = shl_varname
  # TODO: number
  css['td.blob-code > span.pl-k,div.highlight > pre > span.pl-k'] = shl_keyword
  css['td.blob-code > span.pl-c, td.blob-code > span.pl-c > span, div.highlight > pre > span.pl-c, div.highlight > pre > span.pl-c > span'] = shl_comment
  css['td.blob-code > span.pl-v,td.blob-code > span.pl-smi, div.highlight > pre > span.pl-v, div.highlight > pre > span.pl-smi'] = shl_varname
  css['td.blob-code > span.pl-s, div.highlight > pre > span.pl-s'] = shl_string
  css['code.syntax-highlighted-line span.pl-k'] = shl_keyword
  css['code.syntax-highlighted-line span.pl-c, code.syntax-highlighted-line span.pl-c > span'] = shl_comment
  css['code.syntax-highlighted-line span.pl-v,code.syntax-highlighted-line span.pl-smi,code.syntax-highlighted-line span.pl-en'] = shl_varname
  css['code.syntax-highlighted-line span.pl-s'] = shl_string
  css['pre > span.enscript-comment'] = shl_comment
  css['pre > span.enscript-reference'] = shl_preproc
  css['pre > span.enscript-string'] = shl_string
  css['pre > span.enscript-function-name'] = shl_varname
  css['pre > span.enscript-keyword'] = shl_keyword
  css['pre > span.enscript-type'] = shl_varname
  css['pre > span.comment'] = shl_comment
  css['pre > span.keyword'] = shl_keyword
  css['pre > span.variable'] = shl_varname
  css['pre > span.string'] = shl_string
  css['pre > span.ln'] = shl_preproc
  css['div.react-file-line > span.pl-c'] = shl_comment
  css['div.react-file-line > span.pl-k'] = shl_keyword
  css['div.react-file-line > span.pl-v'] = shl_varname
  css['div.react-file-line > span.pl-en'] = shl_varname
  css['div.react-file-line > span.pl-s'] = shl_string
  css['div.react-file-line > span.pl-c1'] = shl_preproc
  css['div#copilot-button-positioner textarea.react-blob-textarea[aria-readonly="true"]']={'**z-index':'-9'} # allow syntax-highlighted version to show through
  css['.FileContents .u-pre span.com'] = shl_comment
  css['.FileContents .u-pre span.kwd'] = shl_keyword
  css['.FileContents .u-pre span.typ'] = shl_varname
  css['.FileContents .u-pre span.str'] = shl_string
  css['div.diff-content .line_content span.k'] = shl_keyword # GitLab merge-requests
  css['div.diff-content .line_content span.n'] = shl_varname
  css['div.diff-content .line_content span.nv'] = shl_varname
  css['div.diff-content .line_content span.nt'] = shl_keyword
  css['div.diff-content .line_content span.ni'] = shl_preproc
  css['div.diff-content .line_content span.na'] = shl_varname
  css['div.diff-content .line_content span.s'] = shl_string
  css['div.diff-content .line_content span.s2'] = shl_string
  css['div.diff-content .line_content span.cp'] = shl_preproc
  css['div.diff-content .line_content span.c1'] = shl_comment
  css['div.diff-content .line_content span.c'] = shl_comment
  css['div.diff-content .line_content span.cm'] = shl_comment
  css['span.blob-code-inner > span.pl-ent'] = shl_varname
  css['span.blob-code-inner > span.pl-kos'] = shl_preproc
  css['span.blob-code-inner > span.pl-s1'] = shl_varname
  css['span.blob-code-inner > span.pl-s'] = shl_string
  css['span.blob-code-inner > span.pl-c'] = shl_comment
  css['devsite-code span.com'] = shl_comment
  css['devsite-code span.kwd'] = shl_keyword
  css['devsite-code span.typ'] = shl_varname
  css['devsite-code span.str'] = shl_string
  css['div.code-view td.lines-code code span.nx'] = shl_varname
  css['div.code-view td.lines-code code span.c1'] = shl_comment
  css['div.code-view td.lines-code code span.kc'] = shl_keyword
  css['div.code-view td.lines-code code span.k'] = shl_keyword
  css['div.code-view td.lines-code code span.s'] = shl_string
  css['.mw-geshi span.kw4'] = shl_keyword
  css['.mw-geshi span.kw1'] = shl_varname
  css['.mw-geshi span.co1'] = shl_comment
  css['.mw-geshi span.coMULTI'] = shl_comment
  css['.mw-geshi span.co2'] = shl_preproc
  css['.mw-geshi span.st0'] = shl_string
  css['code.text-sm > span.token[style="color: rgb(106, 153, 85);"]'] = shl_comment
  css['code.text-sm > span.token[style="color: rgb(86, 156, 214);"]'] = shl_keyword
  css['code.text-sm > span.token[style="color: rgb(220, 220, 170);"]'] = shl_varname
  css['code.text-sm > span.token[style="color: rgb(206, 145, 120);"]'] = shl_string
  css['code span.token.macro'] = shl_preproc
  css['code span.token[style="color: rgb(92, 99, 112); font-style: italic;"]'] = shl_comment
  css['code span.token[style="color: rgb(198, 120, 221);"]'] = shl_keyword
  css['code span.token[style="color: rgb(97, 175, 239);"]'] = shl_varname
  css['code span.token[style="color: rgb(152, 195, 121);"]'] = shl_string
  css['code span.token.keyword'] = shl_keyword
  css['code span.token.function'] = shl_varname
  css['code span.token.string'] = shl_string
  css['code span.token.comment'] = shl_comment
  css['code span.hljs-keyword,code span.hljs-type'] = shl_keyword
  css['code span.hljs-title,code span.hljs-built_in'] = shl_varname
  css['code span.hljs-string'] = shl_string
  css['code span.hljs-comment'] = shl_comment
  css['div.ace_line > span.ace_keyword'] = shl_keyword
  css['div.ace_line > span.ace_identifier'] = shl_varname
  css['div.ace_line > span.ace_comment'] = shl_comment
  css['div.ace_line > span.ace_string'] = shl_string
  
  # Hack for Vodafone UK's login 2012 (stop their mousein/mouseout events going crazy with our layout)
  css["ul#MUmyAccountOptions"]={"*display":"block"}
  # Hack for some authoring tools that use <FONT COLOR=..> to indicate special emphasis
  css["font[color],span[style=\"color: rgb(128, 0, 0);\"],span[style=\"color:red\"],span[style=\"color:rgb(255,0,0)\"]"]={"color":colour["coloured"]}
  printOverride["font[color],span[style=\"color: rgb(128, 0, 0);\"],span[style=\"color:red\"],span[style=\"color:rgb(255,0,0)\"]"]={"color":"black"} # TODO: shade of grey?
  # and others that use span class="Apple-style-span"
  css["span.Apple-style-span"]={"color":colour["coloured"]}
  printOverride["span.Apple-style-span"]={"color":"black"} # TODO: shade of grey?
  # Hack for pinyinannotator
  if pixelSize:
    css["div.interlinear tt"]={"display":"inline-table","line-height":"1.02","text-align":"center","padding":"0.3em"}
    css["div.interlinear tt i"]={"display":"table-row-group","text-align":"center"}
    css["div.interlinear tt i.line1"]={"display":"table-header-group","text-align":"center","color":colour["headings"]}
    printOverride["div.interlinear tt i.line1"]={"color":"black"}
    css["div#container div#result tt"]={"display":"inline-table","line-height":"1.02","text-align":"center","padding":"0.3em"}
    css["div#container div#result tt > i"]={"display":"table-header-group","text-align":"center"}
    css["div#container div#result tt > b, div#container div#result tt > acronym"]={"display":"table-row-group","text-align":"center"}
  # hack for messages on some sites
  css["tr.new td,tr td.new"]={"border-left":"thick solid "+colour["coloured"]}
  css["tr.new td,tr td.new"]={"border-right":"thick solid "+colour["coloured"]}
  # and as that also matches GitLab diffs:
  css["tr.old td,tr td.old"]={"border-left":"thin solid "+colour["coloured"]}
  css["tr.old td,tr td.old"]={"border-right":"thin solid "+colour["coloured"]}
  # and while we're at it:
  css['div.diff-content .line_content span.idiff'] = {"color":colour["coloured"]}
  # hack for (some versions of) phpBB
  css["ul.profile-icons li span"]={"*display":"inline"}
  # hack for embedded Google Maps. 2012-07 Google Maps iframe with certain settings + Safari + CSS = consume all RAM and hang; many sites use GM to embed a "how to find us" map which isn't always the main point of the page, so turn these off until we can fix them properly; in the meantime if you want to see Google Maps you have to turn off this stylesheet (which you'd have to do ANYWAY even without this hack if you want to get any sense out of the maps, unless we can figure out how to give them enough layout exceptions)
  css["body.kui > div#main > div#inner > div#infoarea + div#page > /*div#le-container + div +*/ div#main_map, div.googlemaps > div.mapsbord, div#divMapContainer.MapSingle > div#divMapTools.MapTools, div#divMapContainer.MapSingle > div#divMapTools.MapTools + div#divMap"]={"*display":"none"}
  css["div#mapDiv div"]={"**background":"transparent"}
  css["div.rsltDetails > div.jsDivMoreInfo.hideObj"]={"*display":"block"} # not 'reveal address only when mouse-over' (which might be OK in conjunction with a map but...)
  
  # css['agm-map div[style^="z-index: 3"]']={"**opacity":"0"} # Sopra UKVCAS 2021-05: stops total map occlusion (but still some)
  css['agm-map div']={"**background":"transparent"} # stops more map occlusion, but markers become squares
  css['div#splash-screen + div img']={'**z-index':'9'} # Instagram previews (in Private/Incognito mode: not tried creating an account or anything: beware it's a Facebook property)

  css['body > div#preso, body > div#preso div']={"**background":"transparent"} # Preso training courses
  css['body > div#ada-entry > div:empty']={"**background":"transparent"} # Zoom webinar registrations
  css['div#bilibili-player div']={"**background":"transparent"}
  css['div.bpx-player-video-area div']={"**background":"transparent"}
  css['body > span.pointer-events-none.fixed:empty']={"**background":"transparent"}
  
  make_like_link = ["a.gwt-Anchor"]
  css["casc-crsid"]={"background":colour["background"]} # CamCORS 7
  make_like_link += ["ul.sidebar-navigation > li.sidebar-navigation-item > div.sidebar-navigation-item-header > div.columns:not(:empty)",'a[data-target]'] # ott.cl.cam.ac.uk
  css[','.join(make_like_link)] = css["a:link "] ; css[','.join([(x+":hover") for x in make_like_link])] = css["a:link:hover "]
  printOverride[','.join(make_like_link)] = printOverride["a:link "]
  if (pixelSize and separate_adjacent_links_at_other_sizes) or (not pixelSize and separate_adjacent_links_at_size_0):
    for l in [":before",":after"]:
      css[','.join([(x+l) for x in make_like_link])] = css[exclude_ie_below_9+"a:link"+l]
      printOverride[','.join([(x+l) for x in make_like_link])] = printOverride[exclude_ie_below_9+"a:link"+l]
  css['img[src="img/otterlogo.jpg"][width="100%"]']={'*display':'none'} # ott.cl.cam.ac.uk
  # and ds-print top-up 2017:
  css['body#ext-element-1 div.x-boundlist-floating']={'*position':'relative',"**background":colour["background"]}

  # hack for MHonarc and similar setups that put full-sized images into clickable links
  # (see comments on max-width above; doesn't seem to be a problem in this instance)
  # if pixelSize: css["a:link img,a:visited img"]={"max-width":"100%","max-height":"100%"}
  # -> DON'T do this - if one dimension is greater than 100% viewport but other is less, result can be bad aspect ratio

  # More autocomplete stuff
  css['body > div.jsAutoCompleteSelector[style~="relative;"]'] = {'*position':'relative','border':'blue solid',"**background":colour["background"]}
  
  # hack for sites that use jump.js with nav boxes
  jjc = "body > script + div#wrapper "
  jumpjsContent = jjc+"#content,"+jjc+"div#message"
  jumpjsTooltip = 'div > div.tooltip.dir-ltr[dir="ltr"]' # TODO: ? div[style^="position: absolute"] > div > div.tooltip
  css[jumpjsTooltip+","+jjc+"div#message,"+jjc+"div#toolbarFrame div#standardSearch > form.searchForm > div.suggestions"]={"border":"thin solid "+colour["italic"]}
  for lr in ['Left','Right']: css["div.nav > div.resultNavControls > ul > li.resultNav"+lr+"Disabled"]={'display':'none'}
  if pixelSize:
      css[jumpjsTooltip]={"position":"absolute","z-index":"9","max-width":"20em","left":"1em"}
      css[jjc+"div#toolbarFrame div#standardSearch > form.searchForm > div.suggestions"]={"position":"fixed","z-index":"9"}
      css[jumpjsTooltip+" p,"+jumpjsTooltip+" div.par"]={"margin":"0px","padding":"0px"}
      css["div.document > div.par > p.sl,div.document > div.par > p.sz"]={"margin":"0px","padding":"0px"}
      css["body > script + div#wrapper > div#header, body > script + div#wrapper > div#regionHeader"]={
        "height":"40%", # no more or scroll-JS is too far wrong
        "position":"fixed","top":"0px","left":"auto",
        "right":"0px", # right, not left, or overflow problems, + right helps w. tooltips
        "width":"30%", # not fixed+100% or PgDn will go wrong
        "overflow":"auto","border":"blue solid","z-index":"1",
        "display":"flex","flex":"auto","flex-direction":"row","flex-wrap":"wrap", # seems this is the only way of ensuring no horizontal scroll on Firefox 47 2017-03 (not sure how their JS messes us up otherwise but it does)
      }
      css[jumpjsContent]={"margin-right":"31%","z-index":"0"} # to match the 30% (i.e. take 70%, actually 69%)
      css[jjc+"div#secondaryNavContent"]={"*display":"block"} # not None, even if the screen SEEMS to be too small, because we've changed the layout
      css[jjc + "div#secondaryNav"]={"position":"fixed", # or double-scroll JS fails
                 "bottom":"0px","top":"auto",
                 "right":"0px","left":"auto",
                 "width":"30%","height":"60%","border":"blue solid","overflow":"auto","z-index":"2",
                 "display":"flex","flex":"auto","flex-direction":"row","flex-wrap":"wrap", # same as above
      }
      css["body > div#wrapper #content div#navScrollPositionFloating"]={
        "display":"block", # don't flash on/off
      }
      css[jjc+"#content div#navScrollPositionFloating,"+jjc+"div.navPosition > div.scrollPositionDisplay"]={
        "position":"fixed", # don't 'pop up' using display toggle and disrupt the vertical positioning of the entire text due to our position:static override
        "top":"auto", # because we're using bottom:0px (overriding the popup location)
        "bottom":"0px","right":"0px",
        "width":"30%", # to match the above
        "border":"thin blue solid",
        "overflow":"auto", # just in case
        "z-index":"3", # ditto
      }
      css[jjc+"div.navPosition,"+jjc+"div#primaryNav > div"]={"display":"block"} # as above, don't flash on/off (and don't use inline-block as it creates too much horizontal scrolling)
      css[jjc+"div#regionHeader div.navPosition > div.scrollPositionDisplay"]={
        "position":"static", # as it's inside regionHeader; no point putting it bottom/right or it won't be visible (clipped by regionHeader)
        "width":"100%", # not 30% because this time it's of regionHeader not of screen
      }

      css["body.HomePage > div#regionMain > div.wrapper > div.wrapperShadow > div#slider > div#slideMain"]={"width":"1px","height":"1px","overflow":"hidden"} # can't get those kind of JS image+caption sliders to work well in large print so might be better off cutting them out (TODO somehow relocate to end of page?) (anyway, do height=width=1 because display:none or height=width=0 seems to get some versions of WebKit in a loop and visibility:hidden doesn't always work)
  # and not just if pixelSize (because these icons aren't necessarily visible with our colour changes) -
  emptyLink(exclude_ie_below_9+"li#menuNavigation.iconOnly > a > span.icon","Navigation",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"li#menuNavigation.iconOnly > a","Navigation",css,printOverride,colour)
  emptyLink(exclude_ie_below_9+"li#menuSearchHitNext.iconOnly > a > span.icon","Next hit",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"li#menuSearchHitNext.iconOnly > a","Next hit",css,printOverride,colour)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav > ul.menu > li#menuToday > a.todayNav > span.icon","Today",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav > ul.menu > li#menuPublications > a > span.icon","Publications",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav > div#menuHome > a[aria-label=\"home\"] > span.icon","Home",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav div#compactSearch span.searchIcon.menuButton > span.icon","Search",css,printOverride,colour,False)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav > ul.menu > li#menuHome > a > span.icon","Home",css,printOverride,colour,isInsideRealLink=True)
  emptyLink(exclude_ie_below_9+"div#wrapper div#primaryNav > ul.menu > li#menuHome + li > a > span.icon","Bbl",css,printOverride,colour,isInsideRealLink=True)
  emptyLink("div#wrapper div#documentMenuButton > span.icon","Show...",css,printOverride,colour,False)
  emptyLink("div#wrapper div#documentMenuButton > span.rubyIndicator > span.icon","Romanisation...",css,printOverride,colour,False)
  emptyLink("button#fontSizeSmaller > span.icon","smaller",css,printOverride,colour,False) # probably won't work if we're fixing the size in user CSS, but display anyway to avoid completely empty "Show..." sections if no other functions are shown
  emptyLink("button#fontSizeLarger > span.icon","bigger",css,printOverride,colour,False)
  css[exclude_ie_below_9+"div#header div#menuFrame ul.menu li#menuSynchronizeSwitch a span.icon:after, div#regionHeader menu li#menuSynchronizeSwitch a:after, div#wrapper div#primaryNav ul.menu li#menuSynchronizeSwitch > a#linkSynchronizeSwitch > span.icon:empty:after, div#wrapper div#toolbarFrame ul.menu li#menuSynchronizeSwitch > a#linkSynchronizeSwitch > span.icon:empty:after, li#menuSynchronizeControls li#menuSynchronizeSwitch > a#linkSynchronizeSwitch:empty:after"]={"content":'"Sync"',"text-transform":"none"}
  css[exclude_ie_below_9+"li#menuToolsPreferences.iconOnly > a > span.icon:after"]=css[exclude_ie_below_9+"li#menuToolsPreferences.iconOnly > a:empty:after"]={"content":'"Preferences"',"text-transform":"none"}
  css[exclude_ie_below_9+"div.resultNavControls > ul > li.resultNavLeft > a > span:after, div.jcarousel-container + div#slidePrevButton:empty:after"]={"content":'"<- Prev"',"text-transform":"none"}
  css[exclude_ie_below_9+"div.resultNavControls > ul > li.resultNavRight > a > span:after, div.jcarousel-container + div#slidePrevButton:empty + div#slideNextButton:empty:after"]={"content":'"Next ->"',"text-transform":"none"}
  css[exclude_ie_below_9+"div.resultNavControls > ul > li.resultNavLeft"]={"margin-left":"0px","margin-right":"1ex"}
  css[exclude_ie_below_9+"div.resultNavControls > ul > li.resultNavRight"]={"margin":"0px"}
  css[exclude_ie_below_9+"div.resultNavControls > ul > li.resultNavDoubleLeft > a > span:after"]={'content':'"<<- Backwd"','text-transform':'none'}
  css[exclude_ie_below_9+'div.resultNavControls > ul > li.resultNavDoubleRight > a > span:after']={'content':'"Fwd ->>"','text-transform':'none'}
  css[jumpjsContent.replace(","," .hl,")+" .hl"]={"background":colour["highlight-bkg"]}
  printOverride[jumpjsContent.replace(","," .hl,")+" .hl"]={"background":'white'} # TODO: shade of grey?
  css[jjc+"span.mk, "+jjc+"span.mk b"]={"background":colour["reset-bkg"]}
  printOverride[jjc+"span.mk, "+jjc+"span.mk b"]={"background":"white"}
  css[jjc+"div.stdPullQuote"]={"border":css["aside"]["border"]}
  css['div.jsDownloadFileList ul.downloadItemSet > li.itemRow'] = { # confusion re is the Play button above or below the item: delineate them more clearly
    '*padding-top':'1em', # TODO: does this even work?
    'border':'thin blue solid'}
  css['#content > div#pubListResults > div#pubsViewResults > div.publication'] = {'border':'thin blue solid'}
  css[jjc+"span.pageNum[data-no]"]={'display':'none'}
  css['div.ui-dialog,div[style^="position: fixed"]:not(style~="width: 0%;"),div.js-sticky,div.tooltip']={'**background':colour["background"],'**border':'blue solid'} # these can be opaque (but omit width 0% as some sites use it for not-visible-yet shopping-cart popups)
  css['#content > div#videoPlayerInstance, #content > div#videoPlayerInstance div, div.video-js > div,div.video-js > div.vjs-text-track-display > div:empty']={'**background':'transparent'} # for 0.css
  css['div#regionMain div.tooltip > ul.tooltipList > li.tooltipListItem > div.header > a > span.source + span.title:before']={'content':r'"\2014"'}
  css['div#materialNav > nav > h1 + ul.directory > li > a span.title + span.details,nav ul.books > li.book > a span.name + span.abbreviation'] = {'*float':'right'}
  css['nav ul.books > li.book > a span.name + span.abbreviation + span.official'] = {'*display':'none'}
  css["nav a > img.thumbnail"] = {"*max-height":"1em"}
  css['div.billboard-media-image[style^="background-image"]:empty']={'min-height':'1em'} # (CSS has no way to say "background-image whatever the site set" as an exception: best we can do is make sure this doesn't take up the whole of the first screen in large print)
  # if pixelSize: css[exclude_ie_below_9+"script + div#wrapper > div#header > div#menuFrame > ul.menu > li:before"]={"content":"attr(id)","text-transform":"none","display":"inline"}
  css[".menu li a span.label"]={"display":"inline","text-transform":" none"} # not just 'if pixelSize', we need this anyway due to background overrides
  css["body > script + div#wrapper #content figure > img, div.lsrBannerImage img"]={"*max-width":"100%"}
  emptyLink("a[role=\"button\"] > span.buttonText",None,css,printOverride,colour,False,omitEmpty=True) # TODO: narrow down the selector so 'a' does not have 'href' etc?
  emptyLink("div.downloadContent div.downloadOptions div.fileTypeButtonContainer a.fileType.current span.buttonText",None,css,printOverride,colour,False,omitEmpty=True,undo=True)
  emptyLink('a[aria-label="home"] > span.icon',"Home",css,printOverride,colour,isInsideRealLink=True)
  css["a:empty"]={"**background":"transparent"} # might be position:absolute over the top of something
  css["a:empty:hover"]={"**opacity":"0.5"}
  css["body > div#default-acx-overlay-container, html.hcfe body > div.modal-backdrop, body > div.content-background:empty"]={"**background":"transparent"} # Google Play Console
  css['div.ace_layer']={"**background":"transparent"} # Amazon Alexa code editor
  css['div.videocontrols[role="none"], div.videocontrols[role="none"] div#controlsContainer, div.videocontrols[role="none"] div#controlsContainer div']={"**background":"transparent"} # Firefox e.g. v85 (see toolkit/content/widgets/videocontrols.js, hidden by DOM Inspector)
  css['body > div#react-root main div,body > div#app article > a[href^="https://twitter.com/"]:first-child:empty ~ * div, body.videoEmbedBody div']={"**background":"transparent"} # Twitter video posts (dozens of nested divs with video positioned underneath) + other embedded videos
  css["div.campl-row, div.campl-row > div.campl-wrap, div.campl-wrap > div#content, div#content > div.campl-content-container"]={"**background":"transparent"} # similarly for Panopto(?) lecture platform used by cl.cam
  css["body.player-v2.v2ui div, body > div.mwPlayerContainer, body > div.mwPlayerContainer div"]={"**background":"transparent"} # and Kaltura videos (used by Oracle)
  css["div.video.wistia_embed, div.video.wistia_embed div"]={"**background":"transparent"}
  # some site JS adds modal boxes to the end of the document, try:
  if pixelSize:
    css["body.yesJS > div.ui-dialog.ui-widget.ui-draggable.ui-resizable, body.yesJS > div.fancybox-wrap[style]"]={"position":"absolute","border":"blue solid"}
    css["body.yesJS > div.fancybox-wrap[style] div.fancybox-close:after"]={"content":"\"Close\""}
    # hack for sites that embed YouTube videos (NASA etc) when using the YouTube5 Safari extension on a Mac (TODO: Safari 6 needs sorting out)
    css["div.youtube5top-overlay,div.youtube5bottom-overlay,div.youtube5info,div.youtube5info-button,div.youtube5controls"]={"background":"transparent"}
    css["div#yt-masthead > div.yt-masthead-logo-container, div#yt-masthead-content > form#masthead-search > button.yt-uix-button.yt-uix-button-default"]={"display":"none"}
    css['div.guide-item-container > ul.guide-user-links.yt-box > li[role="menuitem"], div.guide-channels-content > ul#guide-channels > li[role="menuitem"]']={"display":"inline-block"}
  css['div#player.ytd-watch-flexy div']={'**background':'transparent'} # YouTube itself 2024 (but seek-previews still don't show)
  css['div#content.ytd-app div']={'**background':'transparent'} # YouTube 'shorts'
  css['div.OnePlayer-container div']={'**background':'transparent'}
  css['div[id^="ModalFocusTrapZone"],div[class^="OneUpViewer"] div,div.ms-Overlay']={'**background':'transparent'}
  if not colour["text"]=="black": css['div[class^="pdfContent_"] canvas, canvas.pdf-page']={'background':'white','filter':'invert(1)'}
  emptyLink("div.welcome-wrapper > nav > div.container > div.navbar-header > button.navbar-toggle > span:first-child","Toggle navigation",css,printOverride,colour,False)
  emptyLink("div.btn-group > button#hideNames > i.fa-eye-slash","Hide names",css,printOverride,colour,False)
  emptyLink("div.btn-group > button#showNames > i.fa-eye","Show names",css,printOverride,colour,False)
  # hack for MusOpen:
  css["a.download-icon span.icon-down:empty:after"]={"content":'"Download"',"color":colour["link"]}
  printOverride["a.download-icon span.icon-down:empty:after"]={"color":"black"}
  css['iframe[title="Like this content on Facebook."],iframe[title="+1"],iframe[title="Twitter Tweet Button"]']={"*display":"none"}
  # Hack for some other sites that put nothing inside software download links:
  emptyLink("div.jsDropdownMenu.downloadDropdown > a.secondaryButton.dropdownHandle > span.buttonIcon.download","Download",css,printOverride,colour,False)
  emptyLink("a.shareButton > span",None,css,printOverride,colour,False,True);emptyLink("div.standardModal-content > div.itemInfoContainer > div.itemFinderLink > a.copyLink[title=\"Copy Link\"] > span","Copy Link",css,printOverride,colour,False);css["div.itemInfoContainer > div.itemFinderLink, div.itemFinderLink > div.shareLinkContainer,input.shareLink[readonly],div.itemFinderLink > div.shareLinkContainer > input.shareLink"]={"*width":"100%"}
  emptyLink("div#regionHeader + span#contextMenu > span#playSelectedButton span.icon","Play",css,printOverride,colour,False)
  emptyLink("div#regionHeader + span#contextMenu > span#shareContextButton span.icon","Share",css,printOverride,colour,False)
  emptyLink("div#regionHeader + span#contextMenu > span#shareCopyWithCaptionButton span.icon","Copy",css,printOverride,colour,False)
  emptyLink("a[title~=download]","Download",css,printOverride,colour)
  # and more for audio players:
  emptyLink("div.audioFormat > a.stream","Stream",css,printOverride,colour)
  emptyLink("a.jsTrackPlay",r"\21E8 Play",css,printOverride,colour) # (sometimes but not always within div.playBtn)
  emptyLink("a.jsTrackPause","Pause",css,printOverride,colour)
  css["div.jsAudioPlayer div.ui-slider > a.ui-slider-handle:link:empty"] = { "*position": "relative", "text-decoration":"none" }
  for jsPlayElem in ['div','a']:
    css["div.jsAudioPlayer > div.jsAudioPlayerInterface > "+jsPlayElem+".jsPlay.controlElem:empty:after"] = { "content": r'"\21E8 Play"', "color":colour["link"]}
    css["div.jsAudioPlayer > div.jsAudioPlayerInterface > "+jsPlayElem+".jsPlay.jsActive.controlElem:empty:after"] = { "content": r'"Playing"', "color":colour["link"]}
  css["div.jsAudioPlayer > div.jsAudioPlayerInterface > div.jsMute.controlElem:empty:after"] = { "content": '"Mute"', "color":colour["link"]}
  printOverride["div.jsAudioPlayer > div.jsAudioPlayerInterface > div.jsMute.controlElem:empty:after"] = { "color":"black" } # (TODO: but do we want to print those controls at all?)
  css["div.jsAudioPlayer > div.jsAudioPlayerInterface > div.controlElem:empty"] = { "cursor":"pointer" }
  css["div.jsAudioPlayer > div.jsAudioPlayerInterface > div.controlElem"] = { "*display":"inline" }
  css["div.jsAudioPlayer > div.jsAudioPlayerInterface > div.controlElem.ui-slider"] = { "*display":"block" }
  css['div.mejs-playpause-button button[title="Play/Pause"]:empty:after'] = {"content":'"Play/pause"'}
  # and more:
  emptyLink("div.digitalPubFormat > a.fileFormatIcon","Pub format",css,printOverride,colour) # digital publication or whatever
  emptyLink("div.audioFormat > a.fileFormatIcon.audio","Audio format",css,printOverride,colour)
  emptyLink('a[target="itunes_store"]',"iTunes shop",css,printOverride,colour)
  emptyLink('a.appStore[href^="https://itunes.apple.com/"]',"Apple shop",css,printOverride,colour)
  emptyLink('a[href^="https://play.google.com/store/apps/"]',"Android shop",css,printOverride,colour)
  emptyLink('a[href^="http://apps.microsoft.com/"]',"Microsoft shop",css,printOverride,colour)
  emptyLink('div#btnPreviousPage.previousPage',"Previous page",css,printOverride,colour,False)
  emptyLink('div#btnNextPage.nextPage',"Next page",css,printOverride,colour,False)
  emptyLink('div.expanderIcon.collapsed',"+ expand",css,printOverride,colour,False)
  emptyLink('div.expanderIcon.expanded',"- collapse",css,printOverride,colour,False)
  emptyLink('a.navButton.prevNav > div.buttonShell',"Previous",css,printOverride,colour,False)
  emptyLink('a.navButton.nextNav > div.buttonShell',"Next",css,printOverride,colour,False)
  emptyLink('a[title="PREVIOUS"]',"Previous",css,printOverride,colour,True)
  emptyLink('a[title="NEXT"]',"Next",css,printOverride,colour,True)
  emptyLink("div.iconOnly + span.share + span.buttonText",None,css,printOverride,colour,False,True)
  # emptyLink('div.toolbar > a.jsZoomIn.zoomIn',"Zoom in",css,printOverride,colour,False);emptyLink('div.toolbar > a.jsZoomOut.zoomOut',"Zoom out",css,printOverride,colour,False) # TODO: somehow let these work? (apparently it's all CSS tricks and we're overriding it)
  emptyLink('div.toolbar > a.jsCloseModal',"Close",css,printOverride,colour,False)
  emptyLink('div.bili-mini-close-icon',"X",css,printOverride,colour,False)
  css["div.galleryCarouselItems"]={"*white-space":"normal"} # not 'nowrap'
  emptyLink('div.tabViews > div.tabControls > a.discoveryTab',"Discovery",css,printOverride,colour,True);emptyLink('div.tabViews > div.tabControls > a.comparisonTab',"Comparison",css,printOverride,colour,True);emptyLink('div.tabViews > div.tabControls > a.xRefTab',"xref",css,printOverride,colour,True) # has href="#" so True; NB these are more likely :blank than :empty, so might not work in all browsers (but don't want to risk removing :empty altogether)
  emptyLink("div.mejs-inner > div.mejs-controls > div.mejs-play > button",r"\21E8 Play",css,printOverride,colour,False)
  emptyLink("div.mejs-inner > div.mejs-controls > div.mejs-pause > button",r"Pause",css,printOverride,colour,False)
  emptyLink(jjc+"div#regionHeader > div#publicationNavigation > div.studyPaneToggle > span.icon","Toggle study pane",css,printOverride,colour,False) # (TODO: on some versions this is effective only if the browser window exceeds a certain width)
  if pixelSize:
    css[jjc+"div#regionMain div#study div.studyPane,div#regionMain > div.wrapper > div.wrapperShadow > div.studyPane"]={"position":"fixed","bottom":"0px","left":"30%","height":"30%","border":"magenta solid","overflow":"auto","z-index":"4"}
    css[jjc+"div#regionMain div#study div.studyPane,div#regionMain > div.wrapper > div.wrapperShadow > div.studyPane > div"]={"display":"flex","flex":"auto","flex-direction":"row","flex-wrap":"wrap"} # workaround for site's Javascript on Firefox accidentally turning it into horizontal-only multicol scroll
    css[jjc+".pub-int ruby"]={"padding":"0 0.35em"}
    css[jjc+"nav div#documentNavigation div.navVerses ul.verses li.verse"]={"display":"inline","margin":"0 0.1ex"}
    css['a[data-book-id],a.chapter']={"display":"inline-block"}
    css['div#regionMain a[data-book-id] span.fullName + span.longAbbrName, div#regionMain a[data-book-id] span.fullName + span.longAbbrName + span.abbrName, div#regionMain a[data-book-id] > div.tocIcons']={"display":"none"}
  else: css['div.bodyTxt p > span']={"position":"static"} # not absolute (otherwise can overprint) (Must include the 'p' here or it misfires on video play controls)
  emptyLink(jjc+"a.hasAudio > span","Audio",css,printOverride,colour,False)
  emptyLink(jjc+"li.verseOutline a.outToggle > span","Outline",css,printOverride,colour,False) # TODO: why won't this match?
  emptyLink("a#jsGalleryNextBtn > div.nextArrow","Next",css,printOverride,colour,False)
  emptyLink("a#jsGalleryPrevBtn > div.prevArrow","Previous",css,printOverride,colour,False)
  emptyLink('button[title^="Compose"] > span.compose-email-icon',"Compose",css,printOverride,colour,False)
  emptyLink('button > span.previous-email-icon',"Previous",css,printOverride,colour,False)
  emptyLink('button > span.next-email-icon',"Next",css,printOverride,colour,False)
  emptyLink('button > span.print-icon',"Print",css,printOverride,colour,False)
  emptyLink('button[title^="Reply"] > span.reply-icon',"Reply",css,printOverride,colour,False)
  emptyLink('button[title^="Reply"] > span.reply-all-icon',"Reply to All",css,printOverride,colour,False)
  emptyLink('button[title^="Forward"] > span.forward-icon',"Forward",css,printOverride,colour,False)
  emptyLink('button > span.delete-icon',"Delete",css,printOverride,colour,False)
  css["div#screenReaderNavLinkTop > p,div#primaryNav > nav > ul > li"]={"*display":"inline"} # save a bit of vertical space
  css["nav p#showHideMenu > a#showMenu > span.icon:empty:after"]={"content":'"showMenu"'}
  css["nav p#showHideMenu > a#hideMenu > span.icon:empty:after"]={"content":'"hideMenu"'}
  css["nav p#showHideMenu > a#goToMenu > span.icon:empty:after"]={"content":'"goToMenu"'}
  css["a[onclick] > span.iconPrint:empty:after"]={"content":'"Print"'}
  css["a > span.iconHelp:empty:after"]={"content":'"Help"'}
  css["div.jwplayer span.jwcontrols > span.jwcontrolbar span.jwplay > span:first-child:before"]={"content":'"Play/pause button: "'} ; css["div.jwplayer span.jwcontrols > span.jwcontrolbar span.jwplay > span:first-child > button"]={"width":'2em'} # (CSS can't put a text label into that button itself, but we can at least put one before it.  Original is done with background graphics etc.  Incidentally, button:empty doesn't work because it does have some whitespace.)
  css["div.jwplayer span.jwcontrolbar,div.jwplayer span.jwcontrols"]={"display":"inline"} # don't hide controls when mouse is not over video (seeing as they're being repositioned outside it)
  css['div#jwplayer > div > div']={'**background':'transparent'}
  css['div.rp__controls__playback[aria-label="Play"]:empty:before']={"content":'"Play/pause"'} # e.g. ABC Classic FM
  css['div.audio > div.play[rv-on-click]:empty:before']={'content':'"\21E8 Play"'}
  css['div.audio > div.pause[rv-on-click]:empty:before']={'content':'"Pause"'}
  css['body > div.ui-draggable > div.ui-dialog-titlebar']={'cursor':'move'}
  css['img.emoji[src$=".svg"]']={"*height":"1em","*max-height":"1em","*width":"1em","*max-width":"1em"}
  def doHeightWidth(css,height,width): css['img[width="%d"][height="%d"],svg[viewBox="0 0 %d %d"]' % (width,height,width,height)]={"*height":"%dpx"%height,"*max-height":"%dpx"%height,"*width":"%dpx"%width,"*max-width":"%dpx"%width} # setting max as well seems to partially work around some Safari 6.1 SVG bugs
  doHeightWidth(css,17,21);doHeightWidth(css,24,25) # better keep these because it could be an image link to a social network whose natural size is full-screen (and some news sites put these right at the top of all their pages)
  doHeightWidth(css,24,32) # some cl.cam pages
  doHeightWidth(css,24,18) # some Tesco pages 2017-11
  for w in [12,15,16,17,18,20,24,26,28,30,32,36,44,48,50,100]: doHeightWidth(css,w,w) # could be navigation icons or similar & there could be very many of them; don't want these to take too much space (e.g. GitHub 'avatars', can be quite simple but still hundreds of pixels big unnecessarily)
  css["div.write-content > textarea#new_comment_field, div.write-content > textarea#issue_body, div.write-content > textarea[id^=\"issuecomment\"], div.div-dropzone > textarea#issue_description, div.div-dropzone > textarea#note_note"]={"*height":"10em","*border":"blue solid"} # GitHub and GitLab (make comment fields a bit bigger)
  css["div.js-suggester-container > div.write-content > div.suggester-container > div.js-suggester"]={"*position":"absolute","**background":colour["background"]}
  css["div.sidebar-wrapper ul.nav-links > li, div.nav-sidebar ul.nav > li"]={"*display":"inline"} # save a bit of vertical space (GitLab etc)
  css["div.issues-other-filters div.dropdown button.dropdown-menu-toggle span.dropdown-toggle-text svg,a#logo span.logo-text svg,body.ui-indigo div.nav-sidebar a div.nav-icon-container svg,body.ui-indigo a.toggle-sidebar-button svg,body.ui-indigo div.breadcrumbs-links svg.breadcrumbs-list-angle,body.ui-indigo svg.caret-down"]={"*display":"none"} # GitLab 2018
  css['body.ui-indigo .custom-control-input']={"**opacity":"1"} # GitLab merge-request checkboxes: please be visible at size=unchanged
  css["a.note-emoji-button > svg.s16, button > svg.s16"]={"*height":"16px","*width":"16px"} # GitLab 2019
  css["form.new-note div.md-area a.zen-control"]={"*display":"none"} # GitLab 2019
  css["div.merge-request div.status-box svg + span.gl-display-none,div.merge-request div.merge-request-details svg + span.gl-display-none"]={"display":"inline","border":"purple solid"} # GitLab 2021,2022 (be clearer about Open / Merged, not just a small SVG icon)
  css['body.ui-indigo a[title="Cancel"] > svg']={"border":"red solid"} # GitLab actions 2023 (hard to get the text to show, but we can at least highlight the control in some way)
  css['#calendar td.fc-widget-content.day-available']={'border':'green solid'}
  css["div.issues-listing div.state.state-closed"]={'color':colour["coloured"],'border':'red solid','font-weight':'bold'} # GitHub: make it slightly more obvious if we're looking at a closed ticket
  css["summary > svg.icon-chevon-down-mktg, details > summary > svg[viewBox=\"0 0 14 8\"]"]={'*display':'none'} # sorry GitHub, it's way too big when in giant print (and don't know why doHeightWidth isn't fixing these)
  for n in range(6): css['div.ContributionCalendar td[data-level="%d"]' % n] = {'background-color':'var(--contribution-default-bgColor-%d)' % n} # GitHub contributions graphs changed to using background-color ~2023-03 and we don't want to override it all (var updated 2025-03)
  # For Hatjitsu (team estimation):
  css["div.bg > div.container > div.content > div.ng-scope > section.cardPanel > div.cards"]={"*border":"thin red solid"}
  css["div.bg > div.container > div.content > div.ng-scope > section.cardPanel > div.cards > div.card"]={"border":"green solid","*padding":"1em"}
  css["div.bg > div.container > div.content > div.ng-scope > section.cardPanel > div.cards > div.card.card--selected"]={"border":"blue solid"}
  # For Jenkins 1.624 (some of it not quite working yet):
  css["body#jenkins > iframe + div#tt[style^=\"z-index: 999; visibility: visible\"]"]={"*position":"absolute","*border":"blue solid","**background":colour["background"]}
  css["body#jenkins > iframe + div#tt[style^=\"z-index: 999; visibility: hidden\"]"]={"*display":"none"}
  emptyLink("div#menuSelector",r"\2193+",css,printOverride,colour,False)
  css["body#jenkins div#breadcrumb-menu.yui-overlay.visible"]={"*position":"absolute","*border":"blue solid","**background":colour["background"]}
  css["body#jenkins div#breadcrumb-menu.yui-overlay-hidden"]={"*display":"none"}
  css["body#jenkins a > img[alt^=\"Failed\"]:before"]={"*content":'"Failed: "'} ; css["body#jenkins a > img[alt^=\"Success\"]:before"]={"*content":'"Success: "'} # (why on earth does the JS *remove* the title attribute when the mouse enters?)
  # For vtiger CRM 6.5.0:
  emptyLink("div#page > div.navbar > div#topMenus > div#nav-inner > div.menuBar > div#headerLinks span.dropdown > a.dropdown-toggle > span.icon-bar:first-child","Preferences etc",css,printOverride,colour,isInsideRealLink=True)
  css["div#page > div.navbar > div#topMenus > div#nav-inner > div.menuBar > div.span9 > ul#largeNav"]={"*display":"block"}
  for n in ['listView','relatedList']:
    for t in ["Previous","Next"]:
      emptyLink("button#"+n+t+"PageButton.btn > span",t+" page",css,printOverride,colour,False)
  emptyLink("button.dropdown-toggle.btn > i","Toggle",css,printOverride,colour,False)
  # For Atlassan:
  css["span.aui-avatar img, img.jira-project-avatar-icon, img.jpo-team-field-avatar"]={"*width":"24px","*height":"24px"}
  css["a.aui-sidebar-toggle > span.aui-icon:empty:before"]={'content':r'"\2B04"'}
  css[".ghx-backlog-container .ghx-backlog-header"]={'position':'static'} # not sticky, even at pixelSize=0 + zoom
  css["body#jira > aui-dropdown-menu"]={"**max-height":"50%","**overflow":"scroll"} # works around having to use right-hand scrollbar to see all 'More' options when zoomed in

  css['body.md-skin div#wrapper div.shifts-wrapper div.day-wrapper > button.shift']={'*display':'inline'}
  css['body.md-skin div#wrapper div.shifts-wrapper div.day-wrapper > button.shift + div.separator']={'*display':'none'}
  css['body.md-skin div#wrapper div.shifts-wrapper div#shiftModal img']={'*max-width':'100%','*max-height':'9em'}

  css['body#ChapterPage a.jsHasModalListener']={'color':colour['link']}
  printOverride['body#ChapterPage a.jsHasModalListener']={'color':'black'}
  css['div#secondaryNav div#documentNavigation ul.navigationTabs li.tabItem']={'color':colour['link']}
  css['div#secondaryNav div#documentNavigation ul.navigationTabs li.tabItem.active']={'color':colour['visited'],'border':'thin red solid'}
  printOverride['div#secondaryNav div#documentNavigation ul.navigationTabs li.tabItem']=printOverride['div#secondaryNav div#documentNavigation ul.navigationTabs li.tabItem.active']={'color':'#000080'}
  # Hacks for RoundCube-based webmail sites and some forums:
  for t in ["Reset search","Search modifiers","Show preview pane","Enlarge","Click here to give thanks to this post."]: emptyLink('a[title="'+t+'"]',t,css,printOverride,colour) # (OK 'Enlarge' isn't RoundCube but is used on some MediaWiki sites)
  css[exclude_ie_below_9+"li.unread > a > span.unreadcount:before"]={"content":'" ("',"color":colour["coloured"]}
  css[exclude_ie_below_9+"li.unread > a > span.unreadcount:after"]={"content":'")"',"color":colour["coloured"]}
  css[exclude_ie_below_9+"li.unread > a > span.unreadcount"]={"color":colour["coloured"]}
  css["div#mailboxcontainer > div#folderlist-content ul#mailboxlist > li.mailbox"]={"*display":"inline","*border":"none"} # in case you have a lot of folders (seeing as they're displayed on every screen)
  css["div#mailview-bottom > div#mailpreviewframe > iframe#messagecontframe,body.home > div.container > header#globalMasthead + div.clear + header#localMasthead + div.clear + div#frameStore > iframe,body.back > #content > iframe#ifraResult,body.detailhost > table#detable td#drifdiv > iframe#drif"]={ # 'body.home' etc is for search.lib.cam.ac.uk
      "*height":"25em","*overflow":"visible", # hopefully one of those will work
      "*filter":"none","*opacity":"1"}
  css["body.detailhost > table#detable,body.detailhost > table#detable td#drifdiv"]={"*width":"100%"} # also for search.lib.cam.ac.uk
  css["a#composeoptionstoggle > span.iconlink[title=\"Options\"]:empty:after"]={"content":'"Options"'}
  # Blackwells article feedback:
  emptyLink("a[title=\"Yes\"]","Yes",css,printOverride,colour)
  emptyLink("a[title=\"No\"]","No",css,printOverride,colour)
  # Hacks for eBay:
  css['td#storeHeader']={"*width":"30%"}
  css['td#storeHeader + td.ds-dtd iframe']={"*height":"15em","*filter":"none","*opacity":"1"}
  css['a#gh-la > img#gh-logo']={"*display":"none"} # sorry but it's too big and causes too much horizontal scrolling
  css['div#main + div#spinner > div.spinWrap > p.loader:empty']={'*display':'none'} # Energenie/Sagepay+Paypal 2014-10: please don't spin that line all over the screen and give me a seizure (TODO: would be nice to inspect their scripts to figure out which CSS attributes they were using and consider turning these off globally, but this might require another purchase; the site has timeouts so you can't hang around for too long inspecting how it works)
  # Hacks for LycaMobile online top-up (2014):
  css['iframe[style="height: 1024px;"]']={"*height":"50em","*filter":"none","*opacity":"1"} # (some versions of Firefox can't turn off their misguided scrolling="no" markup AND can't access a context menu to open frame in new tab, so I hope height=50em will be enough; TODO: overflow-y within the iframe like the Twitter-embedded hack below?)
  # Hacks for LinkedIn:
  css['div#post-module > div.post-module-in > form#slideshare-upload-form, div#post-module > div.post-module-in > div#slideshare-upload-callout']={'*display':'none'} # can't get it to work, and a non-working form is just clutter
  css['iframe[src^="https://www.linkedin.com/csp/ads"],iframe[src^="https://ad-emea.doubleclick.net"]']={'*display':'none'} # sorry LinkedIn but they're getting really too cluttered for giant-print navigation
  emptyLink("input.post-link + a.post-link-close","Cancel posting link",css,printOverride,colour) ; emptyLink("a.cancel-file-upload","Cancel file upload",css,printOverride,colour) # I think (not sure how this is supposed to work)
  # Hacks for StackOverflow/etc:
  emptyLink('a[title="delete this comment"]',"Delete this comment",css,printOverride,colour)
  emptyLink('a[title="expand to show all comments on this post"]',"Expand all comments",css,printOverride,colour)
  if pixelSize:
    css['iframe[title^="Facebook Cross Domain"]']={'display':'none'}
    css['iframe[height="90"][scrolling="no"]']={'display':'none'}
    # + for many sites with large transparent.png images:
    css['img[src*="/transparent.png"]']={'display':'none'}
    # + for sites that embed their news in Twitter format:
    css["body > div.twitter-timeline,body > div.twitter-tweet"]={"overflow-y":"auto","height":"100%"} # in case the overflow:auto override to iframe's scrolling=no isn't working
    # + more 'news' fixing:
    css["div#main > article > header + div > div.js-right-rail, body > div.asset_inserts + div + div.main > header.js-header, body > div.asset_inserts + div.main > header.js-header"]={"display":"none"} # Huffington 2017: runaway JS overpopulating it and crashing Firefox (I don't know why this rule still doesn't fix it in Chrome)
    # + for BBC radio player:
    css['div.radioplayer-emp-container > div#empv3[style="width: 1px; height: 1px;"]']={"height":"0px","overflow":"hidden"} # so that player controls are higher up (don't say display:none or it won't play in some browsers)
    css['button.twite__share-button,button.twite__share-button + div.twite__panel,a.twite__share-button']={"display":"none"} # BBC 2016/17: users of social networks already know how to share things; don't need icons that take up whole screen when page is put into large print
    css['form[action^="https://ssl.bbc.co.uk"] > button.p-f-button']={'display':'none'} # doesn't work very well anyway and takes up too much room
  css['span[aria-checked="true"],div[aria-checked="true"],span.cf-gb-single__scale-item[aria-checked="true"]'],css['span.cf-gb-single__scale-item']={'border':'green dotted'},{'border':colour['button-bkg']} # newvista surveys (used by BBC complaints 2023)
  css['div[style^="background-image"] + img']={'**opacity':'1'} # Twitter embedded tweets with images at size=unchanged
  css['body#schedules-day div.programmes-page li#on-now']={"border":"blue solid"}
  css['button.smp__blocklink div.smp__overlay div.smp__message div.smp__cta span.smp__messagetext']={"background":colour["button-bkg"],"border":"red solid","margin":"1em"} # 2018 "listen now" button (easy to miss)
  css['div#msi-modal div.msi-modal__body div.msi-modal__wrap']={"position":"fixed","top":"0px","z-index":"999","border":"solid magenta"} # 2018 sign-in box (don't miss this or nothing works)
  css['button.p_iplayerIcon span.p_hiddenElement']={"display":"block","background":colour["button-bkg"],"border":"red solid","margin":"1em"} # and the button once you've signed in (don't hide this please!)
  css['div.episode-playout div.smp iframe']={"overflow-y":"auto","height":"9em","*filter":"none","*opacity":"1"} # more space please so we can see the button

  # alternative to <wbr/> :
  css['div#regionMain > div.wrapper #content article p span.refID, div#regionMain > div.wrapper #content article h2 span.refID, div#regionMain > div.wrapper #content article h3 span.refID, body > div.ui-dialog div > p > span.refID']={"display":"none"}
  # also use of 'q' adding duplicate quotes:
  css['div#regionMain > div.wrapper #content article q.scrp:before, div#regionMain > div.wrapper #content article q.scrp:after']={'content':'""'}

  css['#standardSearch .searchControlContainer .searchButton'] = {'*width':'auto'} # site was somehow overriding it to a pixel width on Safari 6, cutting off the larger text
  emptyLink("#content > div#banner span.bannerDismissible > span.icon","X",css,printOverride,colour,False)
  emptyLink("#content a.documentMenuActivator > span.documentMenuIcon > span.icon","Document Menu",css,printOverride,colour,False)
  emptyLink("nav > div#vector-main-menu-dropdown","Menu",css,printOverride,colour,False,unchangedSizeOnly=True) # Wikipedia 2023
  css['body.mediawiki div.mw-notification-area-overlay']={'**background':'transparent'} # + editing
  css['input.cdx-checkbox__input']={'**opacity':'1'}
  # HomeSwapper etc:
  css['iframe[style^="display: none"]']={"*display":"none"}

  # sites created at wix.com must have this or their JS will crash on load and not display any content:
  css['div#ReflowTestContainer[style^="width: 1px"]']={"*width":"1px","*height":"1px","*overflow":"hidden"}
  css['div#ReflowTestContainer[style^="width: 1px"] > div#ReflowTestNode']={"*width":"200px"}
  css['div#ReflowTestContainer[style^="width: 1px"] > div#ReflowTestNode > div.ReflowTextInnerNode']={"*width":"10%"}
  # w3schools, since it's often coming up in search results -
  for tht in ["Chrome","Internet Explorer","Internet Explorer / Edge","Firefox","Safari","Opera"]: css['th[title="'+tht+'"]:empty:after']={'*content':'"'+tht+'"'}

  # practicalmandarin and other sites designed by some company: please don't jump around when we're in large print
  css['header.sticky-header']={'*display':'block'}

  # video controls etc
  css['svg[viewBox="0 0 22 22"]']={'*height':'22px','*width':'22px'}
  css['svg[viewBox="0 0 32 32"]']={'*height':'32px','*width':'32px'}
  css['svg[viewBox="0 0 36 36"]']={'*height':'36px','*width':'36px'}
  css['div#streamingAudio.jsAudioPlayer']={"*display":"block"} # please don't change it to display:none in Firefox when it scrolls out of view: doing this causes 'jumpy scrolling'
  css['section > main > div > div > article div']={'**background':'transparent'} # Instagram 2024-01 (no account so not tried logging in, but some videos are visible from Google search results in private mode)
  
  # Chrome view source (you can activate a CSS bookmarklet on it), and Firefox view source:
  css['body > div.line-gutter-backdrop + table span.html-tag, body#viewsource span.start-tag, body#viewsource span.end-tag']={"color":colour["headings"]}
  css['body > div.line-gutter-backdrop + table span.html-attribute-name, body#viewsource span.attribute-name']={"color":colour["bold"]}
  css['body > div.line-gutter-backdrop + table span.html-attribute-value, body#viewsource a.attribute-value:not([href])']={"color":colour["italic"]}
  css['body > div.line-gutter-backdrop + table span.html-comment, body#viewsource span.comment']={"color":colour["form_disabled"]}
  css['body#viewsource span > span[id^=\"line\"]:before']={"*content":'" "',"*display":"block","*font-size":"0","*line-height":"0"} # force line break before line number

  css['body[data-grocery-domain="www.tesco.com"] div#content:before']={'*content':'"WARNING.  Tesco\'s Book-a-Slot Javascript is not tolerant of large-print CSS: it says \'error\' when it tries to update the slot table and finds the positions have changed.  Code that faults when sizes or positions are changed is incredibly bad design and breaks the principles of universality intended by Tim Berners-Lee when he invented the World Wide Web. Therefore, Tesco is, in effect, no longer a website, but a proprietary application that just happens to use Web technologies but not in a way that can be made to play nice for low-vision users.  I have attempted to contact Tesco about this multiple times and received no replies.  Tesco is no longer in partnership with the RNIB and they probably replace their good developers with cheap ones.  Adapting these CSS files to Tesco\'s changes has been a continuous struggle and this 2019 Book-a-Slot incompatibility is just too much.  ALL SUPPORT FOR TESCO IS DEPRECATED and may be REMOVED in a future version of this CSS.  You\'ll have to get your shopping somewhere else."'}
  css['h1:before']={"*content":'""'} # overrides large multi-icon image display in Tesco search results 2016-06 (if not logged in with accessibility mode set)
  css['.basketDeliverySurcharge p:before, p.basketInfo:before, body#delivery div#homeDelivery *:after,body#delivery div#homeDelivery *:before, p.productStatus > span.inBasket:before, div.sideBasketHeader > div.action > h2:before, form#fMaxiBasket > div#errorWrapper > div.errors > div.errorContainer:before, form#fMaxiBasket > div#errorWrapper > div.errors > div.errorContainer *:before, div.checkoutContainer > form#fOrder *:before, div#checkoutConfirmationContainer div.content:before']={"*content":'""'} # and this one is needed even on the supposedly "accessible" version (originally developed in conjunction with the RNIB but since drifted)... I want to throw a banana at a Tesco web developer.  Why do I have to spend hours fixing my CSS just to shop?
  css['div.productLists > ul.products > li.whyNotTry']={'*display':'none'} # 'whyNotTry'? hey Tesco, whyNotTry testing your site with low-vision CSS? :-) Then you might realise the end-2016 variation of that 'whyNotTry' gave 10 screenfuls of useless icons.  Sorry to hide your promotions but if they're THAT much of a mess you'd make more profit without them.
  css['body#favourites div#favouritesHub div#hubTopWrap']={'*display':'none'} # Tesco gets it wrong again: 'favourites' is the wrong word for 'usuals' (if I have to buy cold medicine, that doesn't mean I LIKE the stuff) but more to the point we don't want 10+ screens of extra links (each with overspill images full of supposedly-hidden icons) before getting to the list
  emptyLink('a[title="Basket"] span.icon-cart',"Basket",css,printOverride,colour,isInsideRealLink=True) # Tesco 2017-10
  css['div.secondary-nav__left-section > ul.secondary-nav__list'] = { '*display':'block'} # Tesco strikes again.  In 2017-11 their web design department apparently decided anyone with a narrow window (e.g. due to screen magnification) is not allowed to see their Clubcard vouchers on request.  Every little helps... to frustrate our browsing :-(
  css['.header--sticky .primary-nav__item__panel, .header--sticky .utility-nav .utility-nav__list']={"*display":"block"}; css['div[dojotype="dojox.widget.AutoRotator"]'] = {"*display":"none"} # Not that Sainsbury's web developers were any more helpful.  This fixes their broken scrolling 2016-10.
  css['iframe[src^="https://pp.ephapay.net"]']={'*height':'15em'} # Sainsbury's payment card details (they make it non-scrollable)
  css['iframe[src^="http://127.0.0.1:7396/"]']={'*height':'20em'} # Folding@Home client similar (2023)
  css['div.headerContainer > div#searchResultsDidNotFind:before']={"*content":'""'} # more Tesco image madness
  css['body#delivery div#homeDelivery div#deliverySlots td.reserved div.slotDescription']={"border":"thick solid green"} # (and try to make that a bit clearer)
  css['div.tabs > ul.tabs-header-container > li.tabheader.active > a h2, div.tabs > ul.tabs-header-container > li.tabheader.active > a span']={'color':colour["text"]} # Tesco 2018-02 again (confusing non-functional link as current tab)
  css['a.brand-logo-link[href^="/groceries/"] > svg']={'*display':'none'} # Tesco 2018-11: yes we know whose website we're on: we don't need a logo that takes 2 screens to scroll through, thanks anyway...
  css['div.slim-trade-banner--full-width']={'*display':'none'} # Tesco making the page too wide
  css['div#card-section > iframe#bounty-iframe']={'*height':'20em'} # Tesco payment form is in a non-scrollable iframe 2019-07
  css['body > div#bounty-app > form#bounty-form div.secure-payment span.secure-payment__icon, body > div#bounty-app > form#bounty-form div.secure-payment svg']={'*display':'none'} # otherwise it overprints Tesco's entire payment form with a solid box (2019-07).  I actually sent them a video of this one, but I doubt it will make it as far as the developer team.  (To reproduce the video you'll need to get version 0.9873 of this code, e.g. from https://raw.githubusercontent.com/ssb22/css-generator/2253417d45173df2594d4e8c1bc51822613c3f07/css-generate.py as obviously I added the above 3 lines to work around those particular problems but I expect there will be more problems next time because it seems they keep coming up with new ones.)

  css['body.page-template header.site-header + div.all-site-wrap > div.page-wrap + aside.entry-unrelated']={'*display':'none'} # sorry css-tricks but it was making the article unreadable
  css['div#primisPlayerContainerDiv div#primis_container_div']={'*display':'none'} # ditto video advertising on some sites (controls somehow end up covering the entire screen except at size=unchanged)
  
  css['div.xt_fixed_sidebar + div.g_modal.login_modal']={'*position':'absolute','*z-index':'151','border':'blue solid','padding':'1em',"**background":colour["background"]} # Tsinghua online course login
  css['body.question-page script + div.message-dismissable[style^="position: absolute"]']={'*position':'absolute','border':'blue solid','padding':'1em',"**background":colour["background"]} # StackExchange "insufficient reputation to comment" etc

  css['div#wrap > div.__iklan + header#masthead + main#content > article[id^="single-post"] > div.container > div.entry-main > aside.entry-sidebar'] = {"display":"none"} # zap an ever-expanding "sidebar" that never lets you get to the article
  
  # Internet Archive:
  css["div#position > div#wbCalendar > div#calUnder.calPosition"]={"display":"none"}
  css["a.year-label.activeHighlight:link"]={"background":colour["highlight-bkg"]}

  # FontAwesome by Dave Gandy (used on some sites)
  # has accessibility options but these rules apply when they're not turned on:
  if pixelSize:
    for s,r in [("search","Search"),
                  ("user","User"),
                  ("sign-out","Sign out"),
                  ("twitter","Twitter"),
                  ("facebook","Facebook"),
                  ("google-plus","Google+"),
                  ("weixin","WeChat"),
                  ("trash","Delete"),
                  ("trash-o","Delete"),
                  ("paperclip","Attach"),
                  ("mail-reply","Reply"),
                  ("pencil","Edit"), # usually
                  ("times","X"),
                  ("check","OK"),
                  ]:
      for thing in ["a","button"]:
          emptyLink(thing+" > i.fa.fa-"+s,r,css,printOverride,colour,isInsideRealLink=True)
          css[thing+" > i.fa.fa-"+s+":empty:before"]["content"]='""' # in case the font didn't load
    # and if that doesn't work, try bringing in the icon font if it's there:
    css["a > i.fa:empty:before,button > i.fa:empty:before"]={"font-family":"FontAwesome, "+serif_fonts}
  emptyLink("a.overlay-close","Close",css,printOverride,colour)
  emptyLink("div.bannerContent__closeButton","Close",css,printOverride,colour,False)
  emptyLink("div.bcCloseWrapper > div.bcClose > div:only-child","Close",css,printOverride,colour,False)

  css['li.tooltipListItem a.lnk div.card img.thumbnail[src="/img/publication.png"],li.tooltipListItem a.lnk div.card img.thumbnail[src="/img/placeholder.png"],div.tooltip div.tooltipList li > a.cardContainer > div.cardThumbnail, div.tooltip div.tooltipList li > a.cardContainer > div.cardChevron']={"*display":"none"}
  css['div.tooltip > div.tooltipHeader > div']={"*display":"inline-block"}
  emptyLink('div.tooltip > div.tooltipHeader > div.tooltipClose > div.closeBtn > span.icon','X',css,printOverride,colour,False)
  css['div#wrapper > div#regionMain img.thumbnail']={"*max-width":"1em"}

  css['body.page-template div.toggles > div.nav-toggle:before']={'content':'"Toggle navigation: "',"color":colour["link"],"text-decoration":"underline","cursor":"pointer"} # some 'blog' templates contain just bars done as 3 styled empty DIVs

  css['.fixable_fixed']={"*display":"block","*position":"static"} # Quora (needed especially if using CSS bookmarklet instead of proper installation)

  css['body.article-type-article#body .apester-layer']={'*display':'none'} # sorry The Independent, your delayed 'register' popup is not very accessible (2019-04)

  css['div.quoted-text']={'border':'thin grey solid'} # may help on some forum sites

  css['div#mobileNavTopBar div.navBarControls span.navBarButton-icon, button.accordionButton > span.accordionButton-text + span.accordionButton-icon, div.articleFooterLinks nav a span.buttonIcon, div.articleShareLinks span.buttonIcon, button#mobileTOCHandle span.mobilePaneControl-icon, div.downloadLinks span.buttonIcon svg, button.jsCloseModal span.closeModal svg, div.fileContainer a span svg, span[aria-hidden="true"]']={'*display':'none'} # TODO: why do these add 300px+ Y when we've included the 24px svg in doHeightWidth
  css['div.vjs-audio iframe.vjs-resize-manager']={'*display':'none'}

  css['div.play > div.input > textarea.code']={'*height':'15em','*margin-left':'1em'} # golang package examples

  if not pixelSize:
    if not colour["background"]=="white": css["html#whatsapp-web div[data-ref], html#whatsapp-web canvas, img.qrcode-img"]={"border":"thick solid white"} # Whatsapp Web QR code needs white border for phone app to scan it, ditto RedNote
    css["html#whatsapp-web header + div, html#whatsapp-web header + div div, html#whatsapp-web header + div span"]={"background":"transparent"} # WhatsApp (especially in size=unchanged) supposed to be a translucent overlay or something but ends up blanking out the entire page
    css["html#whatsapp-web div.message-in"],css["html#whatsapp-web div.message-out"]={"border":"thin solid cyan"},{"border":"thin solid green"} # WhatsApp message boundaries
    css['html#whatsapp-web div[class*="color-"], html#whatsapp-web div[class*="color-"] span']={"color":colour["headings"]} # WhatsApp person name in group chat
    css['span[aria-label~="Delivered"] > svg']={"opacity":"0.5"}
    css['span[aria-label~="Read"] > svg']={"border":"thin blue solid"}
    # Confluence:
    css['body#com-atlassian-confluence span.inline-comment-marker']={"color":colour["coloured"]}
    css['body#com-atlassian-confluence span.diff-html-added,body#com-atlassian-confluence span.diff-html-removed,body#com-atlassian-confluence span.diff-html-changed']={"color":colour["italic"]}
    css['div#confluence-ui div#Shortcuts div[role="presentation"],div#confluence-ui div[data-layout-container] div:empty']={'**background':'transparent'}
    # Zimbra: (works with size=unchanged, although in Firefox (at least v69)
    # Compose doesn't work because their Javascript fails to find the correct
    # div to change z-index (why don't they just use classes ??) : this seems
    # to be a bug with Zimbra and Firefox, even when no user CSS is applied)
    css['table.ZToolbarButtonTable div.ImgDelete:empty:before']={'content':'"rm"'}
    css['table.ZToolbarButtonTable div.ImgMoveToFolder:empty:before']={'content':'"mv"'}
    css['table.ZToolbarButtonTable div.ImgPrint:empty:before']={'content':'"prn"'}
    css['table.ZToolbarButtonTable div.ImgReply:empty:before']={'content':'"Rply"'}
    css['table.ZToolbarButtonTable div.ImgReplyAll:empty:before']={'content':'"RAll"'}
    css['table.ZToolbarButtonTable div.ImgForward:empty:before']={'content':'"Fwd"'}
    css['table.ZToolbarButtonTable div.ImgJunkMail:empty:before']={'content':'"Junk"'}
    css['table.ZToolbarButtonTable div.ImgTag:empty:before']={'content':'"Tag"'}
    css['table.ZToolbarButtonTable div.ImgLeftArrow:empty:before']={'content':r'"\2190"'}
    css['table.ZToolbarButtonTable div.ImgRightArrow:empty:before']={'content':r'"\2192"'}
    css['div#z_shell div.Row-selected']={'border':'green solid'}
    css['div#z_shell td > div.ImgTaskCheckbox:empty:before']={'content':r'"\2610"'}
    css['div#z_shell td > div.ImgTaskCheckboxCompleted:empty:before']={'content':r'"\2611"'}
    css['div#z_shell td > div.ImgFlagRed:empty:before']={'content':r'"\1F6A9"'} # U+1F6A9 red flag = \D83D\DEA9
    css['div#z_shell td div.ImgMsgStatusRead:empty:before']={'content':'"R"'}
    css['div#z_shell td div.ImgMsgStatusUnread:empty:before']={'content':'"N"'}
    css['div#z_shell td > div.ImgTaskCheckbox:empty, div#z_shell td > div.ImgTaskCheckboxCompleted:empty, div#z_shell td > div.ImgFlagRed:empty, div#z_shell td div.ImgMsgStatusRead:empty, div#z_shell td div.ImgMsgStatusUnread:empty']={'width':'1em'}
    # Slack app-login with size=unchanged: please don't make the "Launch in Slack" buttons invisible due to badly-coded(?) :after CSS:
    css['.c-button--primary:after']={'visibility':'hidden'}
    css['div > index, div > move, div > interrupt'] = defaultStyle.copy() # LiChess move list
    css['cg-container > svg.cg-custom-svgs']={'background':'transparent'} # LiChess 2023
    css['a.js-user-link > span.note-header-author-name']={"word-wrap":"normal"} # not break-word (Gitlab line comments on pull requests)
  
  css['div[role="checkbox"]']={"border":"thin blue solid","min-width":"1em"}
  
  css['div#htmlContent > title + div.container div.page svg path']={'display':'none'} # Cambridge University Press page backgrounds in books (best at 0px with browser zoom?)

  css['div.stat-cell.n']={'border':'red solid'} # caniuse (TODO: why is text now black-on-black unless mouseover?)
  css['div.stat-cell.y']={'border':'green solid'}

  css['div#pt_checkout_onepage input[type="checkbox"],div#pt_checkout_onepage input[type="radio"],body#SurveyEngineBody input[type="checkbox"],body#SurveyEngineBody input[type="radio"]']={'**opacity':'1','position':'static'} # Claires checkout junk-signup checkbox + Qualtrics surveys: please make current state visible (don't just use colours that might be overridden or not seen)
  css['input.oo-ui-inputWidget-input[type="checkbox"]']={'**opacity':'1'} # e.g. MediaWiki on Wenlin edit pages: please make current state more visible
  css['div.gl-display-flex input[type="checkbox"],div.gl-form-checkbox input[type="checkbox"]']={'**opacity':'1'} # GitLab had the same problem

  css['span.starRating-blank:empty:before']={'opacity':'0.5'} # Yellow Pages

  # Google's cookie-consent 2020-09 in 0.css with zoom is disorienting and requires scrolling down to the Accept button, potentially dozens of times per day unless you give up clearing cookies and let Google track you.
  # css['body#gsr div[aria-modal="true"]']={'**display':'none'} # This works OK for normal search results but can prevent interaction with other features like suggested corrections.  Try allowing the box to remain but making it smaller:
  css['body#gsr div[aria-modal="true"],body#gsr div[aria-modal="true"] > div']={'**background':'transparent'}
  css['body#gsr div[aria-modal="true"] > div:first-child']={'**display':'none'} # don't capture clicks on SERP links
  css['body#gsr div[aria-modal="true"] > div + div + div']={'**max-width':'14em','**position':'fixed','**left':'initial','**top':'initial','**right':'0px','**bottom':'0px'} # float:right doesn't seem to work here
  css['body#gsr div[aria-modal="true"] span > div']={'**max-width':'14em','**border-left':'thin blue solid'}
  css['body#gsr div[aria-modal="true"] span > div button + button']={'**position':'absolute','**top':'0px','**right':'0px'} # the Accept button.  Web designers forget that what may be half a screen of text on their box is 5 screens of text for a low vision user and no we don't want to scroll right to the bottom of it to accept cookies for the thousandth time this year.
  css['html']['overflow']='auto'

  # Glint employment surveys, and Oracle ADF generated pages, on size=unchanged: make checkboxes visible in 'dark mode' please
  css['body.questionnairePage input[type="checkbox"].question, body.fusePlus-container input[type="checkbox"]']={'**opacity':'1','**position':'static','**width':'auto','**height':'auto'}

  css['body#page-mod-wiki-view > svg#acc-colour-overlay:empty,body#page-mod-wiki-edit > svg#acc-colour-overlay:empty']={'**display':'none'} # Moodle at size=unchanged: overlay obscuring entire page when background set

  # Recaptcha:
  css['iframe[title^="recaptcha"]']={'*height':'200em','overflow':'visible','*filter':'none','*opacity':'1'}
  css['img[style^="top:-100%"]']={'*top':'-100%'}
  css['img[style^="top:100%"]']={'*top':'100%'}
  css['img[style^="left:-100%"]']={'*left':'-100%'}
  css['img[style^="left:100%"]']={'*left':'100%'}
  css['table.rc-imageselect-table-33']={'*max-width':'100%'}
  css['table.rc-imageselect-table-33 td.rc-imageselect-tile']={'*max-width':'33%'}
  # test on https://www.google.com/recaptcha/api2/demo

  for t in ["checkbox","radio"]: css['article.survey-page div.'+t+'-button-container > input[type="'+t+'"]']={"**opacity":"1"} # surveymonkey 2021: DO show the radio buttons (overriding opacity even at size=unchanged), seeing as their substitute display is done by colours we don't show
  for t in ["checkbox","radio"]: css['body.ballots form#new_ballot div.question td input[type="'+t+'"]']={"**width":"auto","**height":"auto","**position":"static","**opacity":"1"} # ACCU AGM 2023 (electionbuddy.com)
  
  css['#stockSellApp .currency-symbol']={"**position":"static"} # not absolute (Fidelity NetBenefits stock-options form 2021-09: the currency symbol overprinted the first digit when using CSS at size=unchanged)
  css['div.checkbox > input']={"**margin-left":"0px"} # please don't set negative margin to put it underneath some SVG whose state does not show in these colours

  # Google Docs
  gDocs='body.docs-gm[itemtype="http://schema.org/CreativeWork/DocumentObject"] '
  css[gDocs+'div,'+gDocs+'svg']={'background':'transparent'} # avoid obscuring the canvas at size=unchanged
  if not colour["text"]=="black": css[gDocs+'canvas']={'background':'white','filter':'invert(1)'} # because we can't override the black text except by an invert filter (let's assume any browser capable of running Google Docs is also capable of CSS filter effects)
  css['object']['filter']='none' # override site invert if we've also overridden SVG foreground and background
  
  # Similarly for Feishu / Lark (an online office suite used in China)
  css['div.app-main-container.is-suite div, body > div#root > div.et-container div']={'background':'transparent'}
  if not colour["text"]=="black": css['div.app-main-container.is-suite canvas, body > div#root > div.et-container canvas']={'background':'white','filter':'invert(1)'}
  # and shimo.im
  if not colour["text"]=="black": css['body.lizard-one > div#root canvas']={'background':'white','filter':'invert(1)'}
  # and vis.js
  if not colour["text"]=="black": css['div.vis-network > canvas']={'background':'white','filter':'invert(1)'}
  # and Grafana and Kabana
  css['body.app-grafana.theme-dark *, body#kibana-body *']={'background':'transparent'}
  # and Internet Archive Wayback Machine 2022-11
  css['div#react-wayback-search input + input.rbt-input-hint']={'background':'transparent'}
  
  css['button span.mat-button-wrapper + span.mat-ripple']={'**background':'transparent'} # privacymanager.io

  css['div#app div.page-play div.container-main div#player div']={'**background':'transparent'} # m.v.qq.com

  # some sites using BlueprintJS will "leak" DIVs into the DOM when 'toast' message text is cleared without removing its containing element; if these are left translucent, text gets fainter and fainter...
  css['body > div.bp3-portal > div.bp3-toast-container:empty']={'**display':'none'}

  css['body > div#__next > div.App fieldset[aria-hidden]']={'**display':'none'} # groupleavingcards.com 2023-01 (can't fix their sliders but that's not important if you just write a message on a new page and choose a readable font)

  # Chinese Words Separator extension:
  css['X-P > X-S > X-Z']={'fill':'initial','-webkit-text-fill-color':'initial'} # so it can set its own colours via "color"
  css['X-Z > X-H > X-B[g]']={'border-bottom':'thin blue solid'} # ambiguity notification
  
  css['div#outer > div#cub-monitor > img#cub-monitor-pic'],css['div#outer > div#cub-monitor > canvas#screen']={'display':'none'},{'z-index':'0','border':'grey solid'} # JSBeeb
  css['button.open > svg:only-child']={'border':colour['link']} # johnian used this in 2023, possibly from a template: adding a border was only way to make menu button visible at all

  ao3_warnings = "div#main > ol.work ul.required-tags"
  css[ao3_warnings]={'**border':'thin blue solid','**overflow':'auto'}
  css[ao3_warnings+" span"]={'**word-break':'break-all'}
  for R in "rating-explicit rating-mature rating-notrated warning-yes".split(): css[ao3_warnings+" span."+R]={'**border':'thin red solid'}
  css["body.route-storyReading div.left-rail.affixed,body.route-storyReading div.left-rail.affixed div"]={"**border":"none","**background":"transparent"} # Wattpad 'share' button bar
  css["body.route-storyReading div.new-comment-field textarea"]={"**border":"thin blue solid"} # make it more obvious
  css["shreddit-post a.absolute"]={"**background":"transparent","**opacity":"0.2"}

  css['body > div.blink-sdk-widget-container']={'**background':'transparent'}

  css['span.MuiTouchRipple-root,div.MuiBox-root']={'**background':'transparent'} # some React sites
  css['body[itemtype="http://schema.org/CreativeWork/DocumentObject"] div[role="main"] div']={'**background':'transparent'} # Google Drive PDF viewer 2023

  css['body.video.displayCover.embed div']={'**background':'transparent'} # BBC Ideas videos 2023
  css['div#bilibiliPlayer div,shreddit-post div,vds-media div']={'**background':'transparent'} # more videos
  css['faceplate-partial + div.grid-container div.masthead *'],css['faceplate-partial + div.grid-container div.masthead div.community-banner:empty']={'**background':'transparent'},{'**background-image':'var(--original-banner)','background-position':'top center','background-size':'contain','background-repeat':'no-repeat'}

  # quotev quizzes 2023
  css['div#quiz_questions div.selected']={'border':'blue solid'}
  css['div#quizResArea span#resPieChart']={'display':'none'}
  css['div#quiz_questions div.opt[style^="background-color:rgba(0,2"]']={'border':'green solid'}
  css['div#quiz_questions div.opt[style^="background-color:rgba(2"]']={'border':'red solid'}
  css['div#quiz_questions div.q']={'border':'thin grey solid'}

  css['body.mainWindow div.conductorContent div._lvv_w:not(._lvv_y)']={'**border':'thick blue groove'} # unread emails on sites that use Outlook on the Web (OWA) 2023-09 (not tested except at size=unchanged, hence **'d)
  css['div[aria-label^="Scheduling assistant"] div[style~="background-color: rgb(247, 247, 247);"]:empty, div.calendarTentative:empty, div.calendarBusy:empty']={'**border':'thick red solid','**z-index':'1'} # OWA 2024-02
  css['div[aria-label^="Scheduling assistant"] div.ms-border-color-neutralLight:empty']={'**border':'none'} # no half-hour lines please: it gives phantom arrays to nystagmus patients
  css['div.peekPopup abbr.monthPickerCurrentDay,div.peekPopup div[role="row"] span.ms-bg-color-themeLight[role="gridcell"]']={'**border':'grey solid','**z-index':'1'}
  css['div.oui-savant__viewstack__container__dashboards,div.oui-savant__viewstack__container']={'**background':'transparent'} # Oracle OCI dashboard 2023-09
  css['div#appRoot div.oneplayer-root div.video-engine-container,div#appRoot div.oneplayer-root div.critical-playback-container,div#appRoot div.oneplayer-root div.fluent-critical-ui-container,div#appRoot div.oneplayer-root div.onePlayer-overlay,div#appRoot div.oneplayer-root div.onePlayer-overlay div,div#appRoot div.oneplayer-root div.captions-region']={'**background':'transparent'} # SharePoint videos 2024-02
  css['div.body-layout div.navigation-drawer-container']={'**background':'transparent'}
  css['form[action^="/hcmUI"] div']={'**background':'transparent'}
  css['body > div#__next main.relative > div.h-full > div.w-full']={"**border":"thin blue solid"}
  css['div[jsshadow] span']={'**background':'transparent'} # Google Accounts verification 2023-12
  css['div[jscontroller] ~ iframe + div div[role="document"] div']={'**background':'transparent'} # Google Docs PDF viewer 2023-12

  css['body#kt-body div.chapter-editor .checkbox > input']={'**position':'static','**opacity':'1'} # RR 2023-11

  css['div[aria-checked="true"]:empty:before'],css['div[aria-checked="false"]:empty:before'],css['div[aria-disabled="true"]:empty:before']={"content":r'"\2705"'},{"content":r'"\274C"'},{"opacity":"0.5"} # oj-switch (in Oracle Jet)
  css['form.x1g1 input[type="checkbox"]']={'**opacity':'1','**z-index':'99'}
  css['div#confirmTariff input#checkbox-tandc']={'**position':'static','**width':'auto','**height':'auto'}

  css['body > div.c-sky-toast-container div,div.c-search-result__wrapper + a:last-child'],css['div.ui-datepicker-header > a.ui-datepicker-prev > span, div.ui-datepicker-header > a.ui-datepicker-next > span'],css['div.ui-datepicker-header > a.ui-datepicker-prev:after'],css['div.ui-datepicker-header > a.ui-datepicker-next:before']={'**background':'transparent'},{'**display':'none'},{'**color':colour['link'],'**content':r'"\2190"'},{'**color':colour['link'],'**content':r'"\2192"'} # Benevity 2023-12

  css['section#l-main-content > div.l-ad,section#l-main-content > div.l-ad div']={'**background':'transparent'} # Business Insider
  css['html.bc-iframe video-js div,div[data-pagelet="WatchPermalinkVideo"] div']={'**background':'transparent'}
  css['body > div.cdk-overlay-container']={'**background':'transparent'} # AngularJS
  css['body > aside.up-unity-panel-overlay']={'**background':'transparent'}
  css['div#pinnedBottomCenter > div, div#pinnedMiddleLeft > div, div#pinnedTopRight > div']={'**background':'transparent'} # Planet Computers 2024-08 (still needs too-large window at unchanged layout)
  css['div[class^="MediaWrapper"]:empty']={'**background':'transparent'} # Typescript forms (could do with catching its surrounding div also; at least we get only 50% loss of brightness)
  css['.topic-list .main-link a.title']={'**padding':'0px'} # otherwise multiline topics suffer background overwrite on Discourse forums
  css['html[data-rh] > body > div#app-mount div, html[data-rh] > body > div#app-mount div canvas'],css['html[data-rh] > body > div#app-mount div[role="Menu"],html[data-rh] > body > div#app-mount div[role="menu"],html[data-rh] > body > div#app-mount div[class^="autocomplete"],html[data-rh] > body > div#app-mount div[class^="reactionTooltip"],html[data-rh] > body > div#app-mount div[role="dialog"],html[data-rh] > body > div#app-mount div[role="dialog"] > div:only-child']={'**background':'transparent'},{'**background':colour["background"],'**border':'thin blue solid'} # Discord
  css['div[class*="modeUnreadImportant"]']={'**border':'thin blue solid'} # Discord
  css['body > div#__next > div[data-overlay-container] > main div']={'**background':'transparent'} # c.ai
  css['body > div.flex > nav, body > div.flex > nav div, body > div > ol:empty, div.flex div.sticky div, div[style="width: 0px;"] div']={'**background':'transparent'} # Claude
  css['body.dark > div#root div:empty,body > div#__next ~ div[portal-container] span, body > span.pointer-events-none.fixed:empty'],css['div.ds-button--filled[style^="--ds-button-color: rgba"],div#app-container div#chat-container button.text-purple-500,div#composer-background button[aria-pressed="true"]']={'**background':'transparent'},{'border':'thick orange solid'} # DeepSeek,Qwen,ChatGPT
  css['div#chat-container div.transparent, div#chat-container div.absolute.pointer-events-none'],css['div#chat-container nav.sticky']={'**background':'transparent'},{'border':'thin solid blue','padding':'0px'} # z.ai
  css['body > div#root main#main-content[data-testid="main-content"] div,div[aria-live="polite"][style^="position: absolute"],div[aria-live="polite"][style^="position: absolute"] div']={'**background':'transparent'} # BBC
  css['smp-plugin']={'display':'none'} # sorry BBC, too much confusion with Shadow DOMs interfering with video visibility in Firefox so we're dropping your "watch next" links
  css['body > div#app > div#bolt div']={'**background':'transparent'}

  css['lite-youtube[style^="background-image"]']={"background-image":"attr(background-image)"} # YouTube embedded videos (I'm not sure why this works on Firefox 134 since the attribute setting is not obvious; does not work with generic div)
  css['lite-youtube[style^="background-image"] > button']={'**background':'transparent'}

  css['html.non-touch-device body > div#wrapper:first-child']={'**z-index':'9'} # greenhouse.io scheduler: prevent it appearing behind the body and dimmed out
  css['.full-calendar .fc-body .fc-content-col .fc-bgevent-container .fc-bgevent']={'**border':'blue solid','**opacity':'0.9'} # not 0.3 we can hardly see it
  css['.full-calendar .fc-body .fc-content-col .fc-time-grid-event']={'**border':'green solid'}

  # End site-specific hacks
  css[":root:not(html) svg *"]={"color":colour["text"],"background":colour["background"]} # needed for some UI controls on Firefox 62
  css["input[type=text],input[type=password],input[type=search]"]={"border":"1px solid grey"} # TODO what if background is close to grey?
  css['input:-webkit-autofill,audio']={'-webkit-text-fill-color':'initial'} # make sure our webkit-text-fill-color override doesn't apply in contexts where we can't set the background
  # 'html' overflow should be 'visible' in Firefox, 'auto' in IE7.
  css["html:not(:empty)"]={"*overflow":"visible"}
  # speed up scrolling on Midori (from their FAQ), also avoid colour problems in other browsers on some sites:
  css["*"]={"-webkit-box-shadow":"none","box-shadow":"none"}
  # help Opera 12 and other browsers that don't show keyboard focus -
  css[":focus"]={"outline":colour.get("focusOutlineStyle","thin dotted")}
  
  # Text for the beginning of the CSS file:
  
  # outfile.write("@import url(chrome://flashblock/content/flashblock.css);\n")
  # That needs to be on first line for old Firefox + flashblock plugin (ignored if not present).
  # However, old IE (including IE6 on Windows Mobile 5/6) rejects the entire stylesheet if it sees it.
  # I think most users who want to block Flash either do different things or can install the line themselves
  # so perhaps now keeping it causes more trouble than it's worth.  Commenting out.

  outfile.write("/* %s generated by %s */\n" % (filename,__doc__))
  # (useful to have the original filename for when it's renamed userContent.css etc)
  
  outfile.write("""
/* IMPORTANT NOTE.  These stylesheets are NOT intended for
website authors. They are for browser configuration. Using
them on websites that you author might not be a good idea.
- Silas S. Brown */

/* WARNING: This stylesheet has been automatically generated.
You can edit it if you like, but it would probably be easier
to change the program that generates them.
*/""")

  if pixelSize: outfile.write("""

/* Note: CSS can specify that frames be scrollable but it
cannot specify that frames be resizeable.  This can cause
problems on small screens.  To work around it in Firefox,
go to about:config and set layout.frames.force_resizability
to true.
*/

/* Note that this stylesheet uses absolute point sizes in a
number of different places.  This is not good coding, but
it is necessary with some browsers, to avoid problems when
interacting with author-supplied stylesheets. */""")
  elif not colour["text"]=="black":
    if not preapply_FfxDarkModeExceptions: outfile.write("""

/* In Firefox 61+ remove all lines containing the word
  "FfxDarkModeExceptions"
  if you want sites known to have their own auto-applied
  'dark mode' to be given exceptions from this CSS.  This
  can improve interaction on those sites if our 'dark mode'
  isn't fully caught up with all features of the site, but
  beware it can sometimes result in a brief white flash
  while the site is loading. You also need to set Firefox's
  "Settings - General - Language and Appearance -
  Web site appearance" to "Dark". */

/* FfxDarkModeExceptions""")
    if type(preapply_FfxDarkModeExceptions)==list: pfdmxExtra = preapply_FfxDarkModeExceptions
    else: pfdmxExtra = []
    outfile.write('\n@-moz-document regexp("^(?!about:|chrome:|https?://('+"|".join([
  x.replace(".",r"\.") for x in """
  bsky.app character.ai chat.deepseek.com chatgpt.com www.kimi.com
  claude.ai discord.com duckduckgo.com github.com grid.iamkate.com
  learn.microsoft.com security.microsoft.com outlook.office365.com
  libbyapp.com lichess.org octopus.energy huggingface.co
  ssb22.user.srcf.net www.instagram.com www.itv.com www.channel4.com
  www.jw.org hub.jw.org assetsnffrgf-a.akamaihd.net
  www.newscientist.com www.quotev.com chat.qwen.ai
  www.reddit.com www.tiktok.com www.twitch.tv www.youtube.com x.com
  gitlab.com forum.moonshot.ai
""".strip().split()]+pfdmxExtra)+')).*") {')
    if not preapply_FfxDarkModeExceptions: outfile.write('\nFfxDarkModeExceptions */')
  outfile.write("""

/* Some versions of IE ignore the first entry so: */
.placebo { line-height: normal; } /* should be harmless even if there is a
.placebo - we want line-height normal
anyway - and should validate */

/* :not(:empty) stops IE5+6 from misinterpreting things it can't understand */

/* Repeat ALT tags after images (problematic; see Mozilla bug 292116)
(2005: commenting this out for now because more trouble than it's worth;
only Mozilla 1.0 does it properly; later versions and Firefox don't)
img[alt]:after { content: attr(alt) !important; color: #FF00FF !important; }
*/\n""")

  cssRef = dict([(x,y.copy()) for x,y in css.items()])
  ret = outCss(css,outfile,debugStopAfter,pixelSize)
  css = cssRef

  outfile.write("""@media print {
/*
  Old IE (including IE6 on Windows Mobile 5/6) completely ignores the entire contents of @media, so we need to make screen the default
  and use @media to override for print.
  Making screen the default case and overriding here means original sizes and layouts are NOT preserved for printing
  (which might or might not be wanted).
  W3C's CSS Level 1 specs Section 7.1 showed how to ignore these 'at-rules', so CSS1-only browsers SHOULD be ok.
  PocketIE7 on Windows Mobile 6.1 reads inside the @media for 'color' but not 'background', possibly leading to black on black, so we need a second non-"print" @media block to override it back.
  We also need a second block to override things back for Midori (at least some versions): both color and background.
*/
""")
  # (PocketIE7 also has a habit of displaying the page with a white background while rendering, and applying the CSS's colours only afterwards, even if the CSS is in cache.  PocketIE6 did not do this.  See cssHtmlAttrs option in Web Adjuster for a possible workaround.)
  screen_ReOverride = dict([(x,y.copy()) for x,y in printOverride.items()])
  outCss(printOverride,outfile,0,pixelSize)
  del printOverride
  # and the above-mentioned second override for IE7, Midori etc :
  outfile.write("} @media tv,handheld,screen,projection {\n")
  for k in list(screen_ReOverride.keys()):
    for attr in list(screen_ReOverride[k].keys()):
      assert k in css.keys(), k+" was in printOverride but not css (attr="+attr+")"
      assert attr in css[k].keys(), attr+" was in printOverride["+k+"] but not css"
      if screen_ReOverride[k][attr] == css[k][attr]: del screen_ReOverride[k][attr] # don't need to re-iterate an identical attribute
      else:
        assert attr.replace('*','') in ['color','background','background-color','font-size'], attr+" not identical in "+k
        screen_ReOverride[k][attr] = css[k][attr]
    if not screen_ReOverride[k]: del screen_ReOverride[k]
  for k in list(css.keys()):
    for attr in list(css[k].keys()):
      if css[k][attr]=="transparent":
        # need to re-override exceptions after we re-override main div
        if not k in screen_ReOverride: screen_ReOverride[k] = {}
        elif attr in screen_ReOverride[k]: continue
        screen_ReOverride[k][attr] = css[k][attr]
  outCss(screen_ReOverride,outfile,0,pixelSize)
  # Browser-specific screen overrides:
  webkitScreenOverride.update(webkitGeckoScreenOverride)
  webkitScreenOverride.update(webkitMsieScreenOverride)
  geckoScreenOverride.update(webkitGeckoScreenOverride)
  geckoScreenOverride.update(geckoMsieScreenOverride)
  msieScreenOverride.update(webkitMsieScreenOverride)
  msieScreenOverride.update(geckoMsieScreenOverride)
  doneWebkit = 0
  for d,mediaHack in [ # TODO: tv,handheld,projection on these?
      (webkitScreenOverride,"screen and (-webkit-min-device-pixel-ratio:0)"), # must be first (see below)
      (geckoScreenOverride,"screen and (-moz-images-in-menus:0)"),
      (msieScreenOverride,r"screen\0"), # MSIE 8-10 (TODO: 11?  Edge says Webkit)
      (msieScreenOverride,r"screen\9"), # MSIE 6-7
  ]:
    if d or not doneWebkit:
      outfile.write("} @media "+mediaHack+" {\n")
      outCss(d,outfile,0,pixelSize)
      if not doneWebkit:
        outfile.write("::-webkit-input-placeholder { -webkit-text-fill-color: "+colour["form_disabled"]+" !important; }\n") # bug workaround for Safari 10's Webkit (not present on Safari 6 etc): -webkit-text-fill-color in a DIV element overrides that in ::-webkit-input-placeholder, so better re-specify here (making sure it's at the end)
        doneWebkit=1
  outfile.write("}\n")
  if not pixelSize and not colour["text"]=="black":
    if preapply_FfxDarkModeExceptions: outfile.write("}\n")
    else: outfile.write("""/* FfxDarkModeExceptions
}
FfxDarkModeExceptions */
""")
  if extra_CSS: outfile.write("/* extra_CSS: */\n"+extra_CSS)
  return ret

# Selector prefixes to exclude certain browsers from trying to implement a rule:
exclude_ie_below_7 = "html > "
exclude_ie_below_8 = "html >/**/ body "
exclude_ie_below_9 = ":not(:empty) " # IE8 (and non-CSS3 browsers) don't support :not

def debug_binary_chop(items,chop_results,problem_start=0,problem_end=-1):
  # returns start,end of problem, and any remaining chop_results after narrowing down to 1 item (so can pass the rest to a sublist)
  if problem_end==-1: problem_end=len(items)
  if problem_end==problem_start+1:
    if chop_results and chop_results[0]=="1": assert 0, "Binary chop: Problem persisted when removed whole remaining suspect item (with %d chops remaining). Maybe this isn't a problem that's due to just one thing." % (len(chop_results)-1)
    return problem_start,problem_end,chop_results[1:] # [1:] because important to drop 1 result (expected 'problem didn't persist when removing whole item', then try subdividing and check further results)
  problem_mid = int((problem_end-problem_start)/2)+problem_start
  if not chop_results: return problem_start,problem_mid,"" # try disabling 1st half
  if chop_extra_verification:
    if len(chop_results)==1:
      # verify that disabling 2nd half instead gets opposite result
      return problem_mid,problem_end,""
    if chop_results[0]==chop_results[1]: # shouldn't happen
      assert 0, "Binary chop: chop_extra_verification failed; maybe this isn't a problem we can pin down to just one thing."
    chop_results = chop_results[0]+chop_results[2:] # for code below to work
  if chop_results[0]=="1":
    # problem persisted when 1st half disabled, so recurse on 2nd half
    return debug_binary_chop(items,chop_results[1:],problem_mid,problem_end)
  else:
    # problem did not persist when 1st half disabled, so recurse on 1st half
    return debug_binary_chop(items,chop_results[1:],problem_start,problem_mid)

try: from textwrap import fill
except:
  def fill(x,*args,**kwargs): return x
def outCss(css,outfile,debugStopAfter,pixelSize):
  remove_stars(css,pixelSize)
  fix_MathJax(css)
  attrib_val_elemList = get_rList(css)
  if do_binary_chop: binary_chop(attrib_val_elemList)
  return do_output(make_outList(attrib_val_elemList),outfile,debugStopAfter)

def add_aliases(elem,attribValDict):
    for main,alias in [
        ("background","background-color"),
        ("color","-webkit-text-fill-color"),
        ("color","fill"), # for SVG
        ("transform","-ms-transform"),
        ("transform","-moz-transform"),
        ("transform","-webkit-transform"),
        ("transform","-o-transform"),
        ("opacity","-moz-opacity"),
        ("flex","-webkit-flex"),("flex","-moz-flex"),("flex","-ms-flex")]:
      if main in attribValDict.keys() and not alias in attribValDict.keys():
        if alias=="-webkit-text-fill-color" and elem in [
            "a:first-letter", # Safari 14 visited-links bug
            ]: pass
        elif alias=="-webkit-text-fill-color" and elem in [
            "a:link","a","img","html","div","article","body", # Safari 15 "Live Text" in images
            ]: attribValDict[alias]='initial'
        else: attribValDict[alias]=attribValDict[main]
    if not browser_is_Firefox_73: # Firefox 74+ should NOT use -moz-appearance: none when -webkit-appearance is set for a checkbox etc
      if "-webkit-appearance" in attribValDict.keys() and not attribValDict["-webkit-appearance"]=='listbox': # (Firefox 74 forces white background if -moz-appearance listbox, must set -moz-appearance=none for that as done above, just not for checkboxes etc)
        if "-moz-appearance" in attribValDict["-webkit-appearance"]:
          # it's there to ensure it comes after webkit, so delete any other at
          # same level and we're done
          if "-moz-appearance" in attribValDict.keys():
            del attribValDict["-moz-appearance"]
        else: # override 'none' coming from anywhere
          attribValDict["-moz-appearance"]=attribValDict["-webkit-appearance"]
def remove_stars(css,pixelSize):
  for el in list(css.keys()):
    for prop,value in list(css[el].items()):
      if prop.startswith("**"):
        del css[el][prop]
        if not pixelSize: css[el][prop[2:]] = value
      elif prop.startswith("*"):
        del css[el][prop]
        if pixelSize: css[el][prop[1:]] = value
    if css[el] == {}: del css[el]
def fix_MathJax(css): # (see comments above)
  for k in list(css.keys()):
    if k.find("div.MathJax_Display")>-1: css[k.replace("div.MathJax_Display",".MathJax span.math")]=css[k]
def get_rList(css):
  # For each attrib:val find which elems share it & group them
  rDic={} # maps (attrib,val) to a list of elements that have it
  for elem,attribValDict in list(css.items()):
    add_aliases(elem,attribValDict)
    for i in list(attribValDict.items()):
      rDic.setdefault(i,[]).append(elem.strip())
  return sorted(list(rDic.items()))
def binary_chop(attrib_val_elemList):
    global binary_chop_results
    disable_start,disable_end,binary_chop_results = debug_binary_chop(attrib_val_elemList,binary_chop_results)
    if binary_chop_results:
      # chopping up elements within 1 attribute
      attrib_val_elemList[disable_start][1].sort()
      ds2,de2,binary_chop_results = debug_binary_chop(attrib_val_elemList[disable_start][1],binary_chop_results)
      print("Binary chop: From attribute %s=%s, disabling these elements: %s" % (attrib_val_elemList[disable_start][0][0],attrib_val_elemList[disable_start][0][1],", ".join(attrib_val_elemList[disable_start][1][ds2:de2])))
      del attrib_val_elemList[disable_start][1][ds2:de2]
      if binary_chop_results: assert 0, "Binary chop: You have supplied %d too many chop results.  Back off a bit and see the last few debug prints." % (len(binary_chop_results))
    else:
      print("Binary chop: Disabling these attributes: "+"; ".join([("%s=%s"%(k,v)) for (k,v),e in attrib_val_elemList[disable_start:disable_end]]))
      del attrib_val_elemList[disable_start:disable_end]
def make_outList(attrib_val_elemList):
  # If any element groups are identical, merge contents, but beware to keep some things separate:
  outDic = {}
  for (k,v),elemList in attrib_val_elemList:
    elemLists = [[x] for x in elemList if x.find('::')>-1] # COMPLETELY separate the ::selection markup at all times, to work around browsers ignoring the whole list if they don't like it
    def addIn(elemLists,l):
      flat=set(reduce(lambda a,b:a+b,elemLists,[]))
      elemLists.append([i for i in l if not i in flat])
    addIn(elemLists,[x for x in elemList if x.find(':blank')>-1]) # some Firefox versions need this separated
    addIn(elemLists,[x for x in elemList if x.find(':-moz')>-1]) # just in case
    addIn(elemLists,[x for x in elemList if x.find(':-webkit')>-1]) # just in case
    addIn(elemLists,[x for x in elemList if x.find(':ms-')>-1]) # just in case
    addIn(elemLists,[x for x in elemList if not '*' in x and not '>' in x and x.find(':empty')==-1 and x.find(':not')==-1 and not '[' in x and not '+' in x]) # with IE6, if ANY of the elements in the list use syntax it doesn't recognise ('>', '*' etc), it ignores the whole list, so we need to separate these out
    addIn(elemLists,[x for x in elemList if x.find(':not')==-1]) # for later versions of IE
    addIn(elemLists,elemList) # everything else
    for eList in elemLists:
      if not eList: continue
      eList.sort()
      outDic.setdefault(tuple(eList),{})[k]=v
  return sorted(outDic.items(),lambda x,y,lenOfShortestElem=lenOfShortestElem:cmp(lenOfShortestElem(x[0]),lenOfShortestElem(y[0])))
def lenOfShortestElem(elemList): return (min([len(e) for e in elemList if len(e)]),elemList) # (elemList is already alphabetically sorted, so have that as secondary sort)

def do_output(outList,outfile,debugStopAfter):
  for elemList,style in outList:
    if debugStopAfter:
      # for pedantic debugging, write each rule separately
      for e in elemList:
        outfile.write(e+" {\n")
        l=list(style.items()) ; l.sort()
        for k,v in l:
          outfile.write("   %s: %s !important;\n" % (k,v))
          debugStopAfter -= 1
          if not debugStopAfter: break
        outfile.write("}\n")
        if not debugStopAfter: return 0
      continue
    # else, if not debugStopAfter:
    outfile.write(fill(", ".join([(x.replace(" ","%@%")) for x in elemList]).replace("-","#@#"),break_long_words=False).replace("#@#","-").replace("%@%"," ")) # (don't let 'fill' break on the hyphens, or on spaces WITHIN each item which might be inside quoted attributes etc, just on spaces BETWEEN items)
    outfile.write(" {\n")
    l=list(style.items()) ; l.sort()
    for k,v in l: outfile.write("   %s: %s !important;\n" % (k,v))
    outfile.write("}\n")
  return debugStopAfter

def main():
  global outHTML
  if override_output_filename: outHTML=False
  if outHTML: print("<div id=pregen_download><h3>Download pre-generated low-vision stylesheets</h3><noscript>(If you switch on Javascript, there will be an interactive chooser here.&nbsp; Otherwise you can still choose manually from the links below.)</noscript><script><!-- \ndocument.write('Although Javascript is on, for some reason the interactive chooser failed to run on your particular browser. Falling back to the list below.'); //--></script><br><ul>")
  # (HTML5 defaults script type to text/javascript, as do all pre-HTML5 browsers including NN2's 'script language="javascript"' thing, so we might as well save a few bytes)
  for pixelSize in pixel_sizes_to_generate:
    saidPixels = False
    for i in range(len(colour_schemes_to_generate)):
      scheme,suffix,colour = colour_schemes_to_generate[i]
      filename = override_output_filename
      if not filename: filename="%d%s.css" % (pixelSize,suffix)
      if pixelSize:
        if saidPixels: pxDesc = "%dpx" % pixelSize # not "" as there's a chance the googlebot will mistake all those duplicate-text links for some kind of attack
        else:
          pxDesc = "%d pixels" % pixelSize
          saidPixels = True
      else: pxDesc = "unchanged"
      toPrn="<li><a href=\"%s\" download>%s %s</a>" % (filename,pxDesc,scheme)
      if not outHTML: pass
      elif i==len(colour_schemes_to_generate)-1: print(toPrn+"</li>")
      else: print(toPrn+",")
      do_one_stylesheet(pixelSize,colour,filename)
      if override_output_filename: break
    if not sys.stdout.isatty() or not outHTML:
      if override_output_filename:
        sys.stderr.write("Wrote "+override_output_filename+"\n")
      else:
        sys.stderr.write(str(pixelSize)+" ")
        sys.stderr.flush() # Python 3
    if override_output_filename: break
  if (not sys.stdout.isatty() or not outHTML) and not override_output_filename:
    sys.stderr.write("done\n")
  if not outHTML: return
  print("</ul></div>")
  print("""<script><!--
if(document.all||document.getElementById) {
var newDiv=document.createElement('DIV');
var e=document.createElement('H3'); e.appendChild(document.createTextNode('Download or Try Low Vision Stylesheets')); newDiv.appendChild(e);
newDiv.appendChild(document.createTextNode('Select your size and colour: '));
var sizeSelect=document.createElement('SELECT');
var colourSelect=document.createElement('SELECT');
newDiv.appendChild(sizeSelect); newDiv.appendChild(colourSelect);
var defaultSize=35; if(screen && screen.height) defaultSize=screen.height/(window.devicePixelRatio||1)/18.12; // 36pt 15.1in
""")
  pixel_sizes_to_generate.sort()
  for pixelSize in pixel_sizes_to_generate:
    if pixelSize: pxDesc = str(pixelSize)+" pixels"
    else: pxDesc = "unchanged"
    print("e=document.createElement('OPTION'); e.value='"+str(pixelSize)+"'; e.appendChild(document.createTextNode('"+pxDesc+"')); sizeSelect.appendChild(e); if(defaultSize) sizeSelect.selectedIndex="+str(pixel_sizes_to_generate.index(pixelSize))+"; if(defaultSize<"+str(pixelSize)+") defaultSize=0;")
  for scheme,suffix,colour in colour_schemes_to_generate: print("e=document.createElement('OPTION'); e.value='"+suffix+"'; e.appendChild(document.createTextNode('"+scheme+"')); colourSelect.appendChild(e);")
  def tryStylesheetJS(hrefExpr):
    r = "var e=document.createElement('link');e.id0='ssb22css';e.rel='stylesheet';e.href="+hrefExpr+";if(!document.getElementsByTagName('head'))document.body.appendChild(document.createElement('head'));var h=document.getElementsByTagName('head')[0];if(h.lastChild&&h.lastChild.id0=='ssb22css')h.removeChild(h.lastChild);h.appendChild(e);" # try to avoid spaces because they get written as %20 in the bookmarklet
    if alternate_server_for_https_requests:
      if alternate_server_needs_css_extension: r2=""
      else: r2 = r".replace(/[.]css.*/,'')"
      r = "var c="+hrefExpr+","+r[4:].replace(hrefExpr,"location.protocol=='https:'?'"+alternate_server_for_https_requests+r"'+c.slice(c.search(/[^/]*[.]css/))"+r2+":c",1)
    return r
  # (do NOT put that in a JS function, the 1st link must be self-contained.  and don't say link.click() it's too browser-specific)
  letsEncCheck = ""
  if alternate_server_for_https_requests:
    exception = ""
    if alternate_server_is_letsEncrypt:
      # Add warning.  See https://letsencrypt.org/docs/dst-root-ca-x3-expiration-september-2021/ (Firefox 45: SEC_ERROR_EXPIRED_ISSUER_CERTIFICATE; Mac OS 10.7, Chromium 49: NET::ERR_CERT_DATE_INVALID)
      # (this is in a createTextNode so cannot use HTML or entities, unless we redo that part)
      letsEncCheck=r'"+(function(){var n=navigator.userAgent;var f=n.match(/Firefox\/([1-9][0-9]*)/);if(f&&f[1]<50)return true;f=n.match(/Mac OS X 10[._]([0-9]+([._][0-9]+)?)/);return f&&f[1].replace("_",".")<12.1}()?" **Your old browser will no longer respond to this bookmarklet on https sites** unless you first visit the https version of *this* site and accept its '+"'expired' or 'invalid' certificate: this is due to a change made by the 'Let's Encrypt' certificate company at the end of September 2021."+r' ":"")+"'
  else: exception = ", except for HTTPS sites in recent browsers which block 'mixed content' (my site is not yet able to offer an HTTPS option), and"
  print(r"""
newDiv.appendChild(document.createElement('BR'));
newDiv.appendChild(document.createTextNode('Then press '));
var cssLink=document.createElement("A");
var bookmarkletLink=document.createElement("A");
cssLink.className=bookmarkletLink.className="ssbOk";
// to reduce confusion, deleted "view or", and set it to 'attachment' in .htaccess
cssLink.appendChild(document.createTextNode("save stylesheet's code"));
bookmarkletLink.appendChild(document.createTextNode("Try stylesheet"));
newDiv.appendChild(bookmarkletLink);
newDiv.appendChild(document.createTextNode(" or "));
newDiv.appendChild(cssLink);
newDiv.appendChild(document.createTextNode("."));
newDiv.appendChild(document.createElement("BR"));
newDiv.appendChild(document.createTextNode("You may be able to drag the 'try stylesheet' link to your browser's Bookmarks toolbar and later press it to re-style any web page"""+exception+r""" provided the site does not use a Content-Security-Policy header to block third-party stylesheets (browsers are supposed to exempt 'bookmarklets' from this but many don't)."""+letsEncCheck+r""" Anyway, due both to this problem and to some sites' patchy use of CSS priorities, your override is likely to work better if set it as a user-supplied stylesheet "));
/* (we could create a bookmarklet that injects the CSS by value, but then there would be issues with updating if not allowed to XMLHttpRequest from 3rd party and have to carry the whole value in the bookmarklet, and would still have priorities issue) */
e=document.createElement("A"); e.href="#inst"; e.className="ssbOk"; e.appendChild(document.createTextNode("as described below")); newDiv.appendChild(e);
newDiv.appendChild(document.createTextNode("."));
//newDiv.appendChild(document.createTextNode(" (which also means you won't have to press it each time and it will continue to work if this website moves, or becomes unavailable due to local firewall rules etc). The 'bookmarklet' approach is best for short-term use (public terminals etc) or testing."));
var base=document.location.href; var i;
for(i=base.length-1; i; i--) if(base.charAt(i)=='/') break;
base=base.substring(0,i)+"/";
function update() {
  cssLink.href=base+sizeSelect.options[sizeSelect.selectedIndex].value+colourSelect.options[colourSelect.selectedIndex].value+".css";
  cssLink.download=sizeSelect.options[sizeSelect.selectedIndex].value+colourSelect.options[colourSelect.selectedIndex].value+".css";
  bookmarkletLink.href="javascript:"""+tryStylesheetJS("""'"+cssLink.href+"'""")+"""function makevoid(){}makevoid()";
}
sizeSelect.onchange=update; colourSelect.onchange=update; update();
e=document.getElementById('pregen_download'); e.parentNode.replaceChild(newDiv,e);
if(document.location.href.indexOf("?whatLookLike")>-1) {"""+tryStylesheetJS('cssLink.href')+"""}}
//-->
</script>""") # "  # (comment for emacs)
  # (patchy use of CSS priorities: e.g. setting background: white !important while leaving foreground unchanged, mumble mumble)
  print("(above stylesheets generated by version "+__doc__.split()[-1]+")")

do_binary_chop = False
binary_chop_results = ""
import sys, os
alternate_server_for_https_requests = os.environ.get('CSS_HTTPS_SERVER',None) # for the bookmarklet, if you want to apply it on https pages (which means the CSS itself must be served from https) and your main website isn't on an HTTPS-capable server but there's a secondary (lower-bandwidth) one you can use just for that use-case
alternate_server_needs_css_extension = os.environ.get('CSS_HTTPS_SERVER_USE_EXTENSION',False)
alternate_server_is_letsEncrypt = os.environ.get('CSS_HTTPS_SERVER_IS_LETSENCRYPT',False)

if "version" in sys.argv or "--version" in sys.argv:
  print (__doc__+"\nLicensed under the Apache License, Version 2.0")
elif "adjuster-config" in sys.argv:
  # print out configuration options for Web Adjuster
  # e.g. large-print-websites.appspot.com
  ps = [] ; cs = [] ; ha = []
  for p in pixel_sizes_to_generate:
    if p==0: ps.append("0=unchanged size")
    else: ps.append(str(p)+"="+str(p)+" pixels")
  for d,f,rest in colour_schemes_to_generate:
    cs.append(f+'='+d)
    ha.append('text="%s" bgcolor="%s" link="%s" vlink="%s" alink="%s"' % (rest['text'],rest['background'],rest['link'],rest['visited'],'red'))
  print("adjuster.options.headAppendCSS="+repr('http'+'://'+'ssb22.user.srcf.net/css/%s%s.css;'+','.join(ps)+';'+','.join(cs)))
  print("adjuster.options.cssHtmlAttrs="+repr(';'.join(ha)))
elif "desperate-debug" in sys.argv:
  scheme,suffix,colour = colour_schemes_to_generate[0]
  debugStopAfter=1
  while not do_one_stylesheet(chop_pixel_size,colour,"debug%04d.css" % debugStopAfter,debugStopAfter):
    print("Generated debug stylesheet debug%04d.css" % debugStopAfter)
    debugStopAfter += 1
elif "chop" in sys.argv:
  do_binary_chop = True
  binary_chop_results = "".join(sys.argv[sys.argv.index("chop")+1:])
  scheme,suffix,colour = colour_schemes_to_generate[0]
  filename="%d%s.css" % (chop_pixel_size,suffix)
  do_one_stylesheet(chop_pixel_size,colour,filename)
  print("Generated debug stylesheet: "+filename)
else: main()
