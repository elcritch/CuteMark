#!/usr/bin/env python3

import sys, os, glob, logging, collections
from collections import namedtuple
from pathlib import Path
import xmltodict 
from collections import OrderedDict

import mistune

MarkdownStr, Url = None, None


def filetime(v):
    return time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime(v.stat().st_mtime)) if v.exists() else "" 


class EmbeddedImageRenderer(mistune.Renderer):
    
    def link(self, link, title, content):
        
        print("[link] link:{} title:{} content:{} ".format(link, title, content))
        
        linkresult = super().link(link, title, content)
        
        print("[link result] ",linkresult)
        
        return linkresult

    def image(src, title, alt_text):
        
        print("[image] src:{} title:{} alt:{}".format(src, title, alt_text))
        output = super().image(src, title, alt_text)
        
        print("[image result] output:{}".format(output))
        return output 

def processMarkdown(reportStr:MarkdownStr, baseUrl:Url, customCss:CssStr=None, parseHtml:Bool=True):
    
    renderer = EmbeddedImageRenderer()
    md = mistune.Markdown(renderer=renderer, parse_html=parseHtml)
    
    if not customCss:
        reportStr = "\n\n<style>{}</style>\n\n".format(defaultCss) + reportStr
    
    reportHtmlStr = md.render(reportStr)
    
    return reportHtmlStr


def load_xml(pathurl):
    
    pathurl = Path(str(pathurl))
    
    with pathurl.open('r') as file:
        contents = file.read()
    
    xmldict = xmltodict.parse(contents)
    
    return xmldict

def process(test, args):
    
    try:
        process_test(test, args)
    
    except Exception as err:
        
        logging.exception("Report Error: %s error: %s"%(test.info.short,err))
    
        raise err
    
defaultCss = """
/*
---------------------------------------------------------------
Title: GitHub
Author: Brett Terpstra
Description: Github README style. Includes theme for Pygmentized code blocks.
*/
html,body {
	color: black
}
*:not('#mkdbuttons') {
	margin: 0;
	padding: 0
}

#wrapper {
	font: 13.34px helvetica,arial,freesans,clean,sans-serif;
	-webkit-font-smoothing: subpixel-antialiased;
	line-height: 1.4;
	padding: 3px;
	background: #fff;
	border-radius: 3px;
	-moz-border-radius: 3px;
	-webkit-border-radius: 3px
}
p {
	margin: 1em 0;
    hyphens: none;
	-webkit-hyphens: none;
	white-space: nowrap
}
a {
	color: #4183c4;
	text-decoration: none
}

#wrapper {
	background-color: #fff;
	padding: 30px;
	margin: 15px;
	font-size: 12px;
	line-height: 1.6
}

#wrapper>*:first-child {
	margin-top: 0!important
}

#wrapper>*:last-child {
	margin-bottom: 0!important
}


@media screen {
	
	/*	#wrapper {
	box-shadow: 0 0 0 1px #cacaca,0 0 0 4px #eee
	}
	*/
}

h1,h2,h3,h4,h5,h6 {
	/*	margin: 20px 0 10px;*/
	margin: 2em 0 1em;
	padding: 0;
	font-weight: bold;
	-webkit-font-smoothing: subpixel-antialiased;
	cursor: text
}
h1 {
	font-size: 28px;
	border-bottom: 2px solid #ccc;
	color: #000
}
h2 {
	font-size: 24px;
	border-bottom: 2px solid #ccc;
	color: #000
}
h3 {
	font-size: 18px;
	border-bottom: 1px solid #ccc;
	display: inline; 
	color: #333
}
h4 {
	font-size: 16px;
	display: inline; 
	color: #333
}
h5 {
	font-size: 14px;
	display: inline; 
	color: #333
}
h6 {
	color: #777;
	display: inline; 
	font-size: 12px
}
p,blockquote,table,pre {
	margin: 15px 0;
}
ul {
	padding-left: 30px
}
ol {
	padding-left: 30px
}
ol li ul:first-of-type {
	margin-top: 0
}

hr {
	background: transparent url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAYAAAAECAYAAACtBE5DAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAyJpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADw/eHBhY2tldCBiZWdpbj0i77u/IiBpZD0iVzVNME1wQ2VoaUh6cmVTek5UY3prYzlkIj8+IDx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IkFkb2JlIFhNUCBDb3JlIDUuMC1jMDYwIDYxLjEzNDc3NywgMjAxMC8wMi8xMi0xNzozMjowMCAgICAgICAgIj4gPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4gPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIgeG1sbnM6eG1wPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvIiB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIgeG1sbnM6c3RSZWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZVJlZiMiIHhtcDpDcmVhdG9yVG9vbD0iQWRvYmUgUGhvdG9zaG9wIENTNSBNYWNpbnRvc2giIHhtcE1NOkluc3RhbmNlSUQ9InhtcC5paWQ6OENDRjNBN0E2NTZBMTFFMEI3QjRBODM4NzJDMjlGNDgiIHhtcE1NOkRvY3VtZW50SUQ9InhtcC5kaWQ6OENDRjNBN0I2NTZBMTFFMEI3QjRBODM4NzJDMjlGNDgiPiA8eG1wTU06RGVyaXZlZEZyb20gc3RSZWY6aW5zdGFuY2VJRD0ieG1wLmlpZDo4Q0NGM0E3ODY1NkExMUUwQjdCNEE4Mzg3MkMyOUY0OCIgc3RSZWY6ZG9jdW1lbnRJRD0ieG1wLmRpZDo4Q0NGM0E3OTY1NkExMUUwQjdCNEE4Mzg3MkMyOUY0OCIvPiA8L3JkZjpEZXNjcmlwdGlvbj4gPC9yZGY6UkRGPiA8L3g6eG1wbWV0YT4gPD94cGFja2V0IGVuZD0iciI/PqqezsUAAAAfSURBVHjaYmRABcYwBiM2QSA4y4hNEKYDQxAEAAIMAHNGAzhkPOlYAAAAAElFTkSuQmCC) repeat-x 0 0;
	border: 0 none;
	color: #ccc;
	height: 4px;
	padding: 0
}

nav {
	display: none;

/*	font-family: Georgia,Garamond,serif!important;*/
/*	font-style: italic;*/
/*	font-size: 110% !important;*/
/*	line-height: 1.6em;*/
/*	display: block;*/
/*	margin-left: 1em;*/
	
	background-color: #f8f8f8;
	border: 1px solid #ccc;
/*	font-size: 13px;*/
/*	line-height: 19px;*/
/*	overflow: auto;*/
	padding: 6px 10px;
	border-radius: 3px
}

nav ul li {
    position:relative;
    overflow:hidden;
/*    width:330px;*/
}

nav ul li:after {
    font-size: 120%;
    content:".................";
    text-indent: -1px;
    display:inline;
    letter-spacing:14px;
    float:right;
/*    position:absolute;*/
/*    left:50%;*/
/*    bottom:0px;*/
/*    z-index:-1;*/
    font-weight:bold;
}
nav ul li a {
    display:inline;
    color:#000;
    padding-right:5px;
	padding-left: 0.6em;
}

nav ul li .number {
    float:right;
    font-weight:bold;
    padding-left:5px;
}

.hidden {
	display: none;
}

.checklist ul {
	width: intrinsic;
	list-style:none;
	padding-top: 0px;
	padding-bottom: 0px;
	margin-top: 0px;
	margin-bottom: 0px;

	background-color: #f8f8f8;
	border: 1px solid #ccc;
	font-size: 12px;
	line-height: 19px;
	overflow: auto;
	padding: 6px 10px;
	border-radius: 4px;
}

.checklist code {
	background-color: rgba(0,0,0,0.08);
	border: 1px solid #ccc;
	border-radius: 1px;
}

.checklist ul ul {
	padding-left: 1em;
	border: 0;
}

.checklist li {
	vertical-align:middle;
}

.checklist li::before {
	vertical-align:text-bottom;
	color: rgba(0,0,80,1.0);
	font-size: 183%;
    content: "☐";
    width: 1em;
	height: .5em;
    padding-right: 0.25em;
/*	line-height: .5em;*/
}

.checklist[custom] li::before {
	display: none;
	vertical-align:text-bottom;
}

.checklist[custom] li::first-letter {
	vertical-align:text-bottom;
	color: rgba(0,0,80,1.0);
	font-size: 183%;
    width: 1em;	
	height: .5em;
    padding-right: 0.25em;
/*	line-height: .5em;*/
}

.pagebreak {
	page-break-after:always;	
}

pre>code {
}

#wrapper>h2:first-child {
	margin-top: 0;
	padding-top: 0
}

#wrapper>h1:first-child {
	margin-top: 0;
	padding-top: 0
}

#wrapper>h1:first-child+h2 {
	margin-top: 0;
	padding-top: 0
}

#wrapper>h3:first-child,
#wrapper>h4:first-child,
#wrapper>h5:first-child,
#wrapper>h6:first-child {
	margin-top: 0;
	padding-top: 0
}
a:first-child h1,a:first-child h2,a:first-child h3,a:first-child h4,a:first-child h5,a:first-child h6 {
	margin-top: 0;
	padding-top: 0
}
h1+p,h2+p,h3+p,h4+p,h5+p,h6+p,ul li>:first-child,ol li>:first-child {
	margin-top: 0
}
dl {
	padding: 0
}
dl dt {
	font-size: 14px;
	font-weight: bold;
	font-style: italic;
	padding: 0;
	margin: 15px 0 5px
}
dl dt:first-child {
	padding: 0
}
dl dt>:first-child {
	margin-top: 0
}
dl dt>:last-child {
	margin-bottom: 0
}
dl dd {
	margin: 0 0 15px;
	padding: 0 15px
}
dl dd>:first-child {
	margin-top: 0
}
dl dd>:last-child {
	margin-bottom: 0
}
blockquote {
	border-left: 4px solid #DDD;
	padding: 0 15px;
	color: #777
}
blockquote>:first-child {
	margin-top: 0
}
blockquote>:last-child {
	margin-bottom: 0
}

table {
	border-collapse: collapse;
	border-spacing: 0;
	font-size: 100%;
	font: inherit;
	width: auto;
    margin-left:8%;
    margin-right:8%;
	white-space: nowrap;
}
table th {
	font-weight: bold;
	border: 1px solid #ccc;
	background: rgba(0,0,0,0.10);
	border: 1px solid rgba(0,0,0,0.15);
/*	border-bottom: 2px solid rgba(0,0,80,1.0);*/
	padding: 0.5em 0.5em;
}
table thead {
	border: 1px solid rgba(0,0,80,1.0);	
	border-bottom: 3px double rgba(0,0,80,1.0);
	
}
table td {
	border: 1px solid #ccc;
	/*	padding: 6px 13px*/
	/*	padding: 0em 1em;*/
	padding: 0.1em 1.68em;
}
table tr {
	border-top: 1px solid #ccc;
	background-color: #fff;
}


table tr:nth-child(2n) {
	background-color: rgba(0,0,0,0.07);
}
img {
	max-width: 90%
}
code,tt {
	margin: 0 2px;
	padding: 0 5px;
	white-space: nowrap;
	border: 1px solid #eaeaea;
	background-color: #f8f8f8;
	border-radius: 3px;
	font-family: Consolas,'Liberation Mono',Courier,monospace;
	font-size: 12px;
	color: #333
}
pre>code {
	margin: 0;
	padding: 0;
	white-space: pre;
	border: 0;
	background: transparent
}
.highlight pre {
	background-color: #f8f8f8;
	border: 1px solid #ccc;
	font-size: 13px;
	line-height: 19px;
	overflow: auto;
	padding: 6px 10px;
	border-radius: 3px
}
pre {
	background-color: #f8f8f8;
	border: 1px solid #ccc;
	font-size: 13px;
	line-height: 19px;
	overflow: auto;
	padding: 6px 10px;
	border-radius: 3px
}
pre code,pre tt {
	background-color: transparent;
	border: 0
}
.poetry pre {
	font-family: Georgia,Garamond,serif!important;
	font-style: italic;
	font-size: 110%!important;
	line-height: 1.6em;
	display: block;
	margin-left: 1em
}
.poetry pre code {
	font-family: Georgia,Garamond,serif!important;
	word-break: break-all;
	word-break: break-word;
/*	-webkit-hyphens: auto;*/
/*	-moz-hyphens: auto;*/
/*	hyphens: auto;*/
	white-space: pre-wrap
}
sup,sub,a.footnote {
	font-size: 1.4ex;
	height: 0;
	line-height: 1;
	vertical-align: super;
	position: relative
}
sub {
	vertical-align: sub;
	top: -1px
}

@page {
    counter-increment: page;
    counter-reset: page 1;
    @top-right {
        content: "Page " counter(page) " of " counter(pages);
    }
}

@media print {
	
    p.breakhere {
		page-break-before: always
	}
	
	body {
		background: #fff;
		size:8.5in 11in; 
	    margin-top: 1.5in;
	    margin-bottom: 1.5in;
	}
	
/*	http://css-tricks.com/almanac/properties/p/page-break/ */
/*	http://getbootstrap.com/css/ */
	img,pre,blockquote,table,figure {
		page-break-inside: avoid
	}
	
	#wrapper {
		background: #fff;
		border: 0;
/*		padding: 10px;*/
/*		margin: 10px;*/
	    margin-top: 3in;
	    margin-bottom: 1.5in;
		
		font-size: 8px;
		line-height: 1.2
	}
	
	@page {
	    counter-increment: page;
	    counter-reset: page 1;
	    @bottom-right {
	        content: "Page " counter(page) " of " counter(pages);
	    }
	}
	
	code {
		background-color: #fff;
		color: #333!important;
		padding: 0 .2em;
		border: 1px solid #dedede
	}
	
	img {
		max-width: 85%;
	}
	
	table {
/*		width: auto;*/
/*		width: 70%;*/
	    margin-left:2%;
	    margin-right:2%;
	}
	table td {
		border: 1px solid #ccc;
		padding: 0.1em 1.12em;
	}
	table tr {
		border-top: 1px solid #ccc;
		background-color: #fff;
	}
/*	table tr:nth-child(3n) {
		border-bottom: 2px outset  #ccc;
	}*/
	table tr:nth-child(2n) {
/*		border-left:  2px inset #888;*/
/*		border-right:  2px inset #888;*/
	}
	table tr:nth-child(2n+1) {
/*		border-left:  2px inset #ddd;*/
/*		border-right:  2px inset #ddd;*/
	}
	table tr:nth-child(2n) {
		background-color: #fff;
	}
	
	pre {
		background: #fff
	}
	pre code {
		background-color: white!important;
		overflow: visible
	}

}

@media screen {

	body.inverted {
		color: #eee!important;
		border-color: #555;
		box-shadow: none
	}
	.inverted #wrapper,.inverted hr .inverted p,.inverted td,.inverted li,.inverted h1,.inverted h2,.inverted h3,.inverted h4,.inverted h5,.inverted h6,.inverted th,.inverted .math,.inverted caption,.inverted dd,.inverted dt,.inverted blockquote {
		color: #eee!important;
		border-color: #555;
		box-shadow: none
	}
	.inverted td,.inverted th {
		background: #333
	}
	.inverted h2 {
		border-color: #555
	}
	.inverted hr {
		border-color: #777;
		border-width: 1px!important
	}
	::selection {
		background: rgba(157,193,200,0.5)
	}
	h1::selection {
		background-color: rgba(45,156,208,0.3)
	}
	h2::selection {
		background-color: rgba(90,182,224,0.3)
	}
	h3::selection,h4::selection,h5::selection,h6::selection,li::selection,ol::selection {
		background-color: rgba(133,201,232,0.3)
	}
	code::selection {
		background-color: rgba(0,0,0,0.7);
		color: #eee
	}
	code span::selection {
		background-color: rgba(0,0,0,0.7)!important;
		color: #eee!important
	}
	a::selection {
		background-color: rgba(255,230,102,0.2)
	}
	.inverted a::selection {
		background-color: rgba(255,230,102,0.6)
	}
	td::selection,th::selection,caption::selection {
		background-color: rgba(180,237,95,0.5)
	}
	.inverted {
		background: #0b2531;
		background: #252a2a
	}
	.inverted 
	#wrapper {
		background: #252a2a
	}
	.inverted a {
		color: #acd1d5
	}

}
.highlight .c {
	color: #998;
	font-style: italic
}
.highlight .err {
	color: #a61717;
	background-color: #e3d2d2
}
.highlight .k,.highlight .o {
	font-weight: bold
}
.highlight .cm {
	color: #998;
	font-style: italic
}
.highlight .cp {
	color: #999;
	font-weight: bold
}
.highlight .c1 {
	color: #998;
	font-style: italic
}
.highlight .cs {
	color: #999;
	font-weight: bold;
	font-style: italic
}
.highlight .gd {
	color: #000;
	background-color: #fdd
}
.highlight .gd .x {
	color: #000;
	background-color: #faa
}
.highlight .ge {
	font-style: italic
}
.highlight .gr {
	color: #a00
}
.highlight .gh {
	color: #999
}
.highlight .gi {
	color: #000;
	background-color: #dfd
}
.highlight .gi .x {
	color: #000;
	background-color: #afa
}
.highlight .go {
	color: #888
}
.highlight .gp {
	color: #555
}
.highlight .gs {
	font-weight: bold
}
.highlight .gu {
	color: #800080;
	font-weight: bold
}
.highlight .gt {
	color: #a00
}
.highlight .kc,.highlight .kd,.highlight .kn,.highlight .kp,.highlight .kr {
	font-weight: bold
}
.highlight .kt {
	color: #458;
	font-weight: bold
}
.highlight .m {
	color: #099
}
.highlight .s {
	color: #d14
}
.highlight .na {
	color: #008080
}
.highlight .nb {
	color: #0086b3
}
.highlight .nc {
	color: #458;
	font-weight: bold
}
.highlight .no {
	color: #008080
}
.highlight .ni {
	color: #800080
}
.highlight .ne,.highlight .nf {
	color: #900;
	font-weight: bold
}
.highlight .nn {
	color: #555
}
.highlight .nt {
	color: #000080
}
.highlight .nv {
	color: #008080
}
.highlight .ow {
	font-weight: bold
}
.highlight .w {
	color: #bbb
}
.highlight .mf,.highlight .mh,.highlight .mi,.highlight .mo {
	color: #099
}
.highlight .sb,.highlight .sc,.highlight .sd,.highlight .s2,.highlight .se,.highlight .sh,.highlight .si,.highlight .sx {
	color: #d14
}
.highlight .sr {
	color: #009926
}
.highlight .s1 {
	color: #d14
}
.highlight .ss {
	color: #990073
}
.highlight .bp {
	color: #999
}
.highlight .vc,.highlight .vg,.highlight .vi {
	color: #008080
}
.highlight .il {
	color: #099
}
.highlight .gc {
	color: #999;
	background-color: #eaf2f5
}
.type-csharp .highlight .k,.type-csharp .highlight .kt {
	color: #00F
}
.type-csharp .highlight .nf {
	color: #000;
	font-weight: normal
}
.type-csharp .highlight .nc {
	color: #2b91af
}
.type-csharp .highlight .nn {
	color: #000
}
.type-csharp .highlight .s,.type-csharp .highlight .sc {
	color: #a31515
}

"""
    
    