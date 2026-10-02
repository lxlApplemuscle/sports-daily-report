\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{myModel}[2024/05/18 AFO oceanTechnology Template]

% choose Languages
\newif\iflangcn
\newif\iflangen
\DeclareOption{cn}{\langcntrue} 
\DeclareOption{en}{\langentrue} 

%% Class and Options
\def\@@ptsize{12pt} % font size
\DeclareOption{9pt}{\def\@@ptsize{9pt}}
\DeclareOption{10pt}{\def\@@ptsize{10pt}}
\DeclareOption{11pt}{\def\@@ptsize{11pt}}
\DeclareOption{12pt}{\def\@@ptsize{12pt}}
\def\@twoside{0} % default as oneside
\DeclareOption{oneside}{\def\@twoside{0}} % one-side document
\DeclareOption{twoside}{\def\@twoside{1}} % two-side document
\ProcessOptions\relax
\LoadClass[a4paper,onecolumn,\@@ptsize]{article}

%% Page Settings
\RequirePackage[inner=2.0cm,outer=2.0cm,top=1.2cm,bottom=3.5cm]{geometry}
\newcommand{\firstfooteradditionalheight}{1mm} % additional height for footer on the first page
\hfuzz=.5em % disable false positive of overfull \hbox

\newcommand*{\TitleName}[1]{\def\@myTitle{#1}}
\newcommand*{\basicInformation}[2]{
	\def\@nameStu{#1}
	\def\@idStu{#2}}
%\newcommand*{\pageNumber}[1]{\def\@pageNumber{#1}} // \pageNumber{\pageref{LastPage}}
\newcommand*{\backgroundName}[3]{
	\def\@picName{#1}
	\def\@picSize{#2}
	\def\@opaName{#3}}

% setting fontspec
\RequirePackage{ctex, CJKutf8, fontspec}
\setCJKmainfont{SimSun}[AutoFakeBold] %用于实现字体加粗
\setCJKsansfont{SimHei}
\setCJKmonofont{FangSong}
\punctstyle{kaiming} % 设置中文标点
\setmainfont[Mapping=tex-text]{Times New Roman} % 西文默认衬线字体(serif)
\setsansfont[Mapping=tex-text]{Arial}  % 西文默认无衬线字体(sans serif)

%% Fonts and Colors
\RequirePackage[T1]{fontenc}
\RequirePackage[usenames,dvipsnames]{xcolor}

%% TikZ Rule
\RequirePackage{tikz}
\usetikzlibrary{fadings, calc}
\newcommand{\tikzrule}[3][]{\tikz{\fill[#1] (0,0) rectangle (#2,#3);}}

% import packages
\RequirePackage{background, graphicx, subfigure, float}
\RequirePackage[numbers, sort]{natbib}
\RequirePackage{titletoc, enumitem, amsmath, booktabs} 
\setenumerate[1]{itemsep=2pt,partopsep=0pt,parsep=\parskip,topsep=0pt}
\setitemize[1]{itemsep=2pt,partopsep=0pt,parsep=\parskip,topsep=0pt}

%% Sections Settings
\RequirePackage[explicit]{titlesec} % explained in https://tex.stackexchange.com/a/292307/234654
\RequirePackage{suffix}
% http://mirrors.ctan.org/macros/latex/contrib/titlesec/titlesec.pdf
\pgfdeclarelayer{background}
\pgfsetlayers{background,main}
\newcommand{\sectionheadname}{Section} % Name for the Section (default as 'Problem')
\newcommand{\boxedsection}[4][blue!20]{{%
		\begin{tikzpicture}[inner sep=0pt, inner ysep=0.3ex]
			\node[anchor=base west] at (0,0) (counter) {#2};
			\path let \p1 = (counter.base east) in node[anchor=base west, text width={\textwidth-\x1-#4}] (content)
			at ($(counter.base east)+(#4,0)$) {#3};
			\begin{pgfonlayer}{background}
				\shade[left color=#1,right color=white] let \p1=(counter.north), \p2=(content.north) in
				(0,{max(\y1,\y2)}) rectangle (content.south east);
			\end{pgfonlayer}
		\end{tikzpicture}
}}
% For numbered section, i.e. \section{}
\titleformat{\section}% <command>
	{\Large\bfseries}% <format>
	{}% <label>
	{0pt}% <sep>
	{\boxedsection{\sectionheadname{} {\Roman{section}}}{#1}{0.33em}}% <before-code>\titleformat{name=\section,numberless}% <command>
	[%
	\vspace{-2.2\baselineskip}\hfill
	]% <after-code>
\titlespacing*{\section}{0em}{2.5\baselineskip}{1\baselineskip}
\titleformat{\subsection}{\large\bfseries}{\arabic{subsection}.}{0.33em}{#1}
\titleformat{\subsubsection}{\large\bfseries}{(\arabic{subsubsection})}{0.33em}{#1}

%% Code Block Settings
\RequirePackage{listings}
\definecolor{gray}{rgb}{0.5,0.5,0.5}
\definecolor{mauve}{rgb}{0.58,0,0.82}
\newfontfamily{\ttconsolas}{Consolas}
\lstset{
	numbers=left,  
	frame=tb,
	aboveskip=3mm,
	belowskip=3mm,
	showstringspaces=false,
	columns=fixed,
	framerule=1pt,
	rulecolor=\color{gray!35},
	backgroundcolor=\color{gray!5},
	basicstyle={\ttconsolas\small},
	numberstyle=\footnotesize\color{gray},
	keywordstyle=\bfseries\color{NavyBlue},
	commentstyle=\color{black!50!white},
	stringstyle=\color{mauve},
	breaklines=true,
	breakatwhitespace=true,
	tabsize=2,
	extendedchars=false,
	postbreak=\mbox{\hspace{-1.4em}\textcolor{purple}{$\hookrightarrow$}\space}
}
%% Captions Settings
\RequirePackage[font=footnotesize,labelfont=bf]{caption}
%% Color Boxes
\RequirePackage[many]{tcolorbox}
\RequirePackage{varwidth}
\newtcolorbox{box1}[2][]{enhanced,skin=enhancedlast jigsaw,
	attach boxed title to top left={xshift=-4mm,yshift=-0.5mm},
	fonttitle=\bfseries\sffamily,varwidth boxed title=0.7\linewidth,
	colbacktitle=blue!45!white,colframe=blue!50!black,
	interior style={color=green!10!white},
	boxed title style={empty,arc=0pt,outer arc=0pt,boxrule=0pt},
	underlay boxed title={
		\fill[tcbcolbacktitle] (title.north west) -- (title.north east)
		-- +(\tcboxedtitleheight-1mm,-\tcboxedtitleheight+1mm)
		-- ([xshift=4mm,yshift=0.5mm]frame.north east) -- +(0mm,-1mm)
		-- (title.south west) -- cycle;
		\fill[tcbcolbacktitle!50!black] ([yshift=-0.5mm]frame.north west)
		-- +(-0.4,0) -- +(0,-0.3) -- cycle;
		\fill[tcbcolbacktitle!50!black] ([yshift=-0.5mm]frame.north east)
		-- +(0,-0.3) -- +(0.4,0) -- cycle; },
	title={#2},#1}
\newtcolorbox{box2}[2][]{enhanced,
	colframe=blue!50!black,colback=blue!10!white,colbacktitle=blue!5!yellow!10!white,
	fonttitle=\bfseries,coltitle=black,attach boxed title to top center=
	{yshift=-0.25mm-\tcboxedtitleheight/2,yshifttext=2mm-\tcboxedtitleheight/2},
	boxed title style={boxrule=0.5mm,
		frame code={ \path[tcb fill frame] ([xshift=-4mm]frame.west)
			-- (frame.north west) -- (frame.north east) -- ([xshift=4mm]frame.east)
			-- (frame.south east) -- (frame.south west) -- cycle; },
		interior code={ \path[tcb fill interior] ([xshift=-2mm]interior.west)
			-- (interior.north west) -- (interior.north east)
			-- ([xshift=2mm]interior.east) -- (interior.south east) -- (interior.south west)
			-- cycle;} },
	title={#2},#1}
\newtcbox{\mybox}[1][red]
{on line, arc = 0pt, outer arc = 0pt,
	colback = #1!10!white, colframe = #1!50!black,
	boxsep = 0pt, left = 1pt, right = 1pt, top = 2pt, bottom = 2pt,
	boxrule = 0pt, bottomrule = 0pt, toprule = 0pt}

% setting abstract
\newcommand{\cnAbstractname}{\LARGE\textbf{Introduction}}
\newenvironment{cnabstract}{%
	\par\large
	\noindent\mbox{}\hfill{\heiti\Large\cnAbstractname}\hfill\mbox{}\par{}\vspace{0.5em}}{}

%% Header and Footer
\RequirePackage{fancyhdr}
\RequirePackage[colorlinks=true, urlcolor=blue, linkcolor=purple, citecolor=red, hypertexnames=false]{hyperref}
\setlength{\headheight}{52pt}
\setlength{\marginparwidth}{2cm}
\pagestyle{fancy}
\if\@twoside0
\lhead{
	\fontfamily{LinuxLibertineT-OsF}\selectfont
	\textsc{\@myTitle}}
\rhead{\thepage}
\renewcommand\headrule{\vspace{-0.7em}\tikzrule[BrickRed, path fading=east]{.5\textwidth}{0.3mm}}
\else
\fancyhf{}
\renewcommand\headrule{%
	\ifodd\thepage
	\vspace{-0.7em}\tikzrule[BrickRed, path fading=east]{.5\textwidth}{0.3mm}
	\else
	\vspace{-0.7em}\hfill\tikzrule[BrickRed, path fading=west]{.5\textwidth}{0.3mm}
	\fi}
\fancyhead[LO]{
	\fontfamily{LinuxLibertineT-OsF}\selectfont
	\textsc{\@myTitle }
	\renewcommand\headrule{\vspace{-0.7em}\tikzrule[BrickRed, path fading=east]{.5\textwidth}{0.3mm}}
}
\fancyhead[RE]{
	\fontfamily{LinuxLibertineT-OsF}\selectfont
	\textsc{\@myTitle }
}
\fancyhead[LE,RO]{\thepage}
\fi
\cfoot{}
% header and footer style for the first page
\fancypagestyle{firstpage}{
	\renewcommand\headrule{}
	\lhead{}
	\rhead{}
	\cfoot{
		\fontfamily{LinuxLibertineT-OsF}\selectfont
		\vspace*{-2.\firstfooteradditionalheight}
		\vspace{-1.5em}
		\tikzrule[purple, path fading=west]{.5\textwidth}{.15em}%
		\tikzrule[purple, path fading=east]{.5\textwidth}{.15em}}}

%% Title Settings
\RequirePackage{tabularx}
\RequirePackage{afterpage}
\makeatletter         
\renewcommand\maketitle{
%	
	\thispagestyle{firstpage}
	\fontfamily{LinuxLibertineT-OsF}\selectfont % set font as Linux Libertine
	\enlargethispage{-\firstfooteradditionalheight} % make room for the footer
	\begin{minipage}[c]{6.5cm}
		\centering
		{\Huge\textcolor{Plum}{\scshape \@myTitle}} \\
		{\textit{Instructor:~\@nameStu}}
	\end{minipage}
	\begin{minipage}{9cm}
		\raggedright
		{\textcolor{Plum}{E-mail:}\textcolor{BrickRed}{\@idStu}} \\
		{\textcolor{Plum}{GitHub:}
		 \textcolor{BrickRed}{https://github.com/lxlApplemuscle/FluidDynamic}}
	\end{minipage} \\
	\tikzrule[cyan, path fading=east]{\textwidth}{.4em}
	
%	\begin{center} 
%		\vspace{-1\baselineskip}\color{RoyalPurple!50!black}
%		\LARGE\S~{Documentation}~\S
%	\end{center} 
%	\fontfamily{cmr}\selectfont % Computer Modern
}
%\makeatother

%setting background
\backgroundsetup{scale=\@picSize,angle=0,opacity=\@opaName,contents={\includegraphics[width=\paperwidth, height=\paperwidth, keepaspectratio]{\@picName}}}

% 图、表、公式样式
% 如果图片没有指定后缀, 依次按下列顺序搜索
\DeclareGraphicsExtensions{.eps,.pdf,.jpg,.png}
\RequirePackage[justification=centering]{caption} 
\captionsetup{figurewithin=section}
\captionsetup{tablewithin=section}
\iflangcn\renewcommand{\figurename}{图}   \fi
\iflangen\renewcommand{\figurename}{Fig}  \fi
\iflangcn\renewcommand{\tablename}{表}    \fi
\iflangen\renewcommand{\tablename}{Table} \fi
\renewcommand\thefigure{\arabic{section}-\arabic{figure}}
\renewcommand\thetable{\arabic{section}-\arabic{table}}
\renewcommand{\labelenumi}{(\theenumi)}
\renewcommand{\captionfont}{\zihao{5}\heiti} 
\numberwithin{equation}{section} 


%% setting ref
%\setcitestyle{authoryear,open={(},close={)}}
%\def\bibfont{\fontsize{10.5pt}{10}\selectfont} 

%% Arrow 
\usetikzlibrary{arrows.meta} 
\newcommand{\SolidImplies}{\mathrel{%
		\tikz[baseline=-0.5ex] \draw[color=., -{Latex[length=2.5mm, width=2mm]}, line width=3.pt, fill=black] (0,0.05) -- (0.6,0.05);%
}}

