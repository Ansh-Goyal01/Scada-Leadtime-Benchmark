%% PHM Society LaTeX Class
%% Based on standard LaTeX article class
%% Created by Jose Celaya, Indranil Roychoudhury, Matthew Daigle
%%
%% Revisions:
%% 	2012/01/15, created

% Class setup
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{PHMSociety}[2013/01/15 v0.01 PHMSociety LaTeX Class]
\LoadClassWithOptions{article}

% TO DO:
% Do we want "draft" modes or similar?
% Clean up of definitions (see comments in those sections)


% ------------------------------------------------------------------------------------------
%
%: PACKAGE REQUIREMENTS
%
% ------------------------------------------------------------------------------------------
\RequirePackage{times}						% font selection
\RequirePackage{fancyhdr}					% for headers/footers
\RequirePackage{flushend}					% evening out final page
\RequirePackage[labelsep=period, format=plain]{caption}
\RequirePackage{wrapfig}					% for biography photos
\RequirePackage[hang,flushmargin]{footmisc} % for footnotes
\RequirePackage{apacite}					% for citation style
\RequirePackage[english]{babel}		% for apacite setup
\RequirePackage{setspace}					% to enforce single spacing of bibliography


% ------------------------------------------------------------------------------------------
%
%: PAGE LAYOUT
%
% ------------------------------------------------------------------------------------------
\twocolumn  								% two column paper
\flushbottom 								% ???

% -- Text body size
\setlength\textheight{9.0in}
\setlength\textwidth{7.0in}

% -- Margins and column separation
% NOTE: The side margins assume that the margin origin is at 1" (\loffset), 
% 		So to make it 0.75", it needs to be set to negative.
% Check for reference: http://help-csli.stanford.edu/tex/latex-margins.shtml
\setlength\evensidemargin{-0.25in} % needed only of "two side" document version is selected, which should not be
\setlength\oddsidemargin{-0.25in}
\setlength\columnsep{0.25in}

% -- Header and top margins
% NOTE: The top margin assume that the origin is at 1" (\voffset) to the top of the header box
% Check for reference: http://help-csli.stanford.edu/tex/latex-margins.shtml
\setlength\topmargin{-0.5in}			% Move up to accommodate header box
\setlength\headheight{0.15in} 			% Header box is 0.5in hight
\setlength\headsep{0.35in}

% --- Title box setup
\newlength\titlebox 					% define new length variable
\setlength\titlebox{3.5in}				% This is a default value only, it might need to be modified in the *.tex file to 
								% account for cases with more affiliations and authors that will require a 
								% bigger box

% To do activities:
% - The "titlebox" work needs user input for cases with extended number of authors. Consider modifying this infrastructure so it is done automatically without the user modifying the "\titlebox" in the *.tex file
% [MD] Consider using geometry package to clean this up? 
% END of PAGE LAYOUT Configuration


% ------------------------------------------------------------------------------------------
%
%: HEADER AND FOOTER CONTENT DECLARATIONS
%
% ------------------------------------------------------------------------------------------

% no header/footer for first page
\thispagestyle{empty}
\pagestyle{fancy}
\fancyhead{}
\fancyfoot{}

% set up publication year, which may be given as an option
\def\publicationYear{20xx}

\DeclareOption{2009}{
\def\publicationYear{2009}
}

\DeclareOption{2010}{
\def\publicationYear{2010}
}

\DeclareOption{2011}{
\def\publicationYear{2011}
}

\DeclareOption{2012}{
\def\publicationYear{2012}
}

\DeclareOption{2013}{
\def\publicationYear{2013}
}

\DeclareOption{2014}{
\def\publicationYear{2014}
}

\DeclareOption{2015}{
\def\publicationYear{2015}
}

\DeclareOption{2016}{
\def\publicationYear{2016}
}

\DeclareOption{2017}{
\def\publicationYear{2017}
}

\DeclareOption{2018}{
\def\publicationYear{2018}
}

\DeclareOption{2019}{
\def\publicationYear{2019}
}

\DeclareOption{2020}{
\def\publicationYear{2020}
}

\DeclareOption{2021}{
\def\publicationYear{2021}
}

\DeclareOption{2022}{
\def\publicationYear{2022}
}

\DeclareOption{2023}{
\def\publicationYear{2023}
}

\DeclareOption{2024}{
\def\publicationYear{2024}
}

\DeclareOption{2025}{
\def\publicationYear{2025}
}

\DeclareOption{2026}{
\def\publicationYear{2026}
}

\DeclareOption{2027}{
\def\publicationYear{2027}
}

\DeclareOption{2028}{
\def\publicationYear{2028}
}

\DeclareOption{2029}{
\def\publicationYear{2029}
}

\DeclareOption{2030}{
\def\publicationYear{2030}
}

% set up paper number, which may be given as an option
\def\paperNumber{000}

\DeclareOption{001}{
\def\paperNumber{001}
}

\DeclareOption{1}{
\def\paperNumber{001}
}

\DeclareOption{01}{
\def\paperNumber{001}
}

\DeclareOption{002}{
\def\paperNumber{002}
}

\DeclareOption{2}{
\def\paperNumber{002}
}

\DeclareOption{02}{
\def\paperNumber{002}
}

\DeclareOption{003}{
\def\paperNumber{003}
}

\DeclareOption{3}{
\def\paperNumber{003}
}

\DeclareOption{03}{
\def\paperNumber{003}
}

\DeclareOption{004}{
\def\paperNumber{004}
}

\DeclareOption{4}{
\def\paperNumber{004}
}

\DeclareOption{04}{
\def\paperNumber{004}
}

\DeclareOption{005}{
\def\paperNumber{005}
}

\DeclareOption{5}{
\def\paperNumber{005}
}

\DeclareOption{05}{
\def\paperNumber{005}
}

\DeclareOption{006}{
\def\paperNumber{006}
}

\DeclareOption{6}{
\def\paperNumber{006}
}

\DeclareOption{06}{
\def\paperNumber{006}
}

\DeclareOption{007}{
\def\paperNumber{007}
}

\DeclareOption{7}{
\def\paperNumber{007}
}

\DeclareOption{07}{
\def\paperNumber{007}
}

\DeclareOption{008}{
\def\paperNumber{008}
}

\DeclareOption{8}{
\def\paperNumber{008}
}

\DeclareOption{08}{
\def\paperNumber{008}
}

\DeclareOption{009}{
\def\paperNumber{009}
}

\DeclareOption{9}{
\def\paperNumber{009}
}

\DeclareOption{09}{
\def\paperNumber{009}
}

\DeclareOption{010}{
\def\paperNumber{010}
}

\DeclareOption{10}{
\def\paperNumber{010}
}

\DeclareOption{011}{
\def\paperNumber{011}
}

\DeclareOption{11}{
\def\paperNumber{011}
}

\DeclareOption{012}{
\def\paperNumber{012}
}

\DeclareOption{12}{
\def\paperNumber{012}
}

\DeclareOption{013}{
\def\paperNumber{013}
}

\DeclareOption{13}{
\def\paperNumber{013}
}

\DeclareOption{014}{
\def\paperNumber{014}
}

\DeclareOption{14}{
\def\paperNumber{014}
}

\DeclareOption{015}{
\def\paperNumber{015}
}

\DeclareOption{15}{
\def\paperNumber{015}
}

\DeclareOption{016}{
\def\paperNumber{016}
}

\DeclareOption{16}{
\def\paperNumber{016}
}

\DeclareOption{017}{
\def\paperNumber{017}
}

\DeclareOption{17}{
\def\paperNumber{017}
}

\DeclareOption{018}{
\def\paperNumber{018}
}

\DeclareOption{18}{
\def\paperNumber{018}
}

\DeclareOption{019}{
\def\paperNumber{019}
}

\DeclareOption{19}{
\def\paperNumber{019}
}

\DeclareOption{020}{
\def\paperNumber{020}
}

\DeclareOption{20}{
\def\paperNumber{020}
}

\DeclareOption{021}{
\def\paperNumber{021}
}

\DeclareOption{21}{
\def\paperNumber{021}
}

\DeclareOption{022}{
\def\paperNumber{022}
}

\DeclareOption{22}{
\def\paperNumber{022}
}

\DeclareOption{023}{
\def\paperNumber{023}
}

\DeclareOption{23}{
\def\paperNumber{023}
}

\DeclareOption{024}{
\def\paperNumber{024}
}

\DeclareOption{24}{
\def\paperNumber{024}
}

\DeclareOption{025}{
\def\paperNumber{025}
}

\DeclareOption{25}{
\def\paperNumber{025}
}

\DeclareOption{026}{
\def\paperNumber{026}
}

\DeclareOption{26}{
\def\paperNumber{026}
}

\DeclareOption{027}{
\def\paperNumber{027}
}

\DeclareOption{27}{
\def\paperNumber{027}
}

\DeclareOption{028}{
\def\paperNumber{028}
}

\DeclareOption{28}{
\def\paperNumber{028}
}

\DeclareOption{029}{
\def\paperNumber{029}
}

\DeclareOption{29}{
\def\paperNumber{029}
}

\DeclareOption{030}{
\def\paperNumber{030}
}

\DeclareOption{30}{
\def\paperNumber{030}
}

\DeclareOption{031}{
\def\paperNumber{031}
}

\DeclareOption{31}{
\def\paperNumber{031}
}

\DeclareOption{032}{
\def\paperNumber{032}
}

\DeclareOption{32}{
\def\paperNumber{032}
}

\DeclareOption{033}{
\def\paperNumber{033}
}

\DeclareOption{33}{
\def\paperNumber{033}
}

\DeclareOption{034}{
\def\paperNumber{034}
}

\DeclareOption{34}{
\def\paperNumber{034}
}

\DeclareOption{035}{
\def\paperNumber{035}
}

\DeclareOption{35}{
\def\paperNumber{035}
}

\DeclareOption{036}{
\def\paperNumber{036}
}

\DeclareOption{36}{
\def\paperNumber{036}
}

\DeclareOption{037}{
\def\paperNumber{037}
}

\DeclareOption{37}{
\def\paperNumber{037}
}

\DeclareOption{038}{
\def\paperNumber{038}
}

\DeclareOption{38}{
\def\paperNumber{038}
}

\DeclareOption{039}{
\def\paperNumber{039}
}

\DeclareOption{39}{
\def\paperNumber{039}
}

\DeclareOption{040}{
\def\paperNumber{040}
}

\DeclareOption{40}{
\def\paperNumber{040}
}

\DeclareOption{041}{
\def\paperNumber{041}
}

\DeclareOption{41}{
\def\paperNumber{041}
}

\DeclareOption{042}{
\def\paperNumber{042}
}

\DeclareOption{42}{
\def\paperNumber{042}
}

\DeclareOption{043}{
\def\paperNumber{043}
}

\DeclareOption{43}{
\def\paperNumber{043}
}

\DeclareOption{044}{
\def\paperNumber{044}
}

\DeclareOption{44}{
\def\paperNumber{044}
}

\DeclareOption{045}{
\def\paperNumber{045}
}

\DeclareOption{45}{
\def\paperNumber{045}
}

\DeclareOption{046}{
\def\paperNumber{046}
}

\DeclareOption{46}{
\def\paperNumber{046}
}

\DeclareOption{047}{
\def\paperNumber{047}
}

\DeclareOption{47}{
\def\paperNumber{047}
}

\DeclareOption{048}{
\def\paperNumber{048}
}

\DeclareOption{48}{
\def\paperNumber{048}
}

\DeclareOption{049}{
\def\paperNumber{049}
}

\DeclareOption{49}{
\def\paperNumber{049}
}

\DeclareOption{050}{
\def\paperNumber{050}
}

\DeclareOption{50}{
\def\paperNumber{050}
}

\DeclareOption{051}{
\def\paperNumber{051}
}

\DeclareOption{51}{
\def\paperNumber{051}
}

\DeclareOption{052}{
\def\paperNumber{052}
}

\DeclareOption{52}{
\def\paperNumber{052}
}

\DeclareOption{053}{
\def\paperNumber{053}
}

\DeclareOption{53}{
\def\paperNumber{053}
}

\DeclareOption{054}{
\def\paperNumber{054}
}

\DeclareOption{54}{
\def\paperNumber{054}
}

\DeclareOption{055}{
\def\paperNumber{055}
}

\DeclareOption{55}{
\def\paperNumber{055}
}

\DeclareOption{056}{
\def\paperNumber{056}
}

\DeclareOption{56}{
\def\paperNumber{056}
}

\DeclareOption{057}{
\def\paperNumber{057}
}

\DeclareOption{57}{
\def\paperNumber{057}
}

\DeclareOption{058}{
\def\paperNumber{058}
}

\DeclareOption{58}{
\def\paperNumber{058}
}

\DeclareOption{059}{
\def\paperNumber{059}
}

\DeclareOption{59}{
\def\paperNumber{059}
}

\DeclareOption{060}{
\def\paperNumber{060}
}

\DeclareOption{60}{
\def\paperNumber{060}
}

\DeclareOption{061}{
\def\paperNumber{061}
}

\DeclareOption{61}{
\def\paperNumber{061}
}

\DeclareOption{062}{
\def\paperNumber{062}
}

\DeclareOption{62}{
\def\paperNumber{062}
}

\DeclareOption{063}{
\def\paperNumber{063}
}

\DeclareOption{63}{
\def\paperNumber{063}
}

\DeclareOption{064}{
\def\paperNumber{064}
}

\DeclareOption{64}{
\def\paperNumber{064}
}

\DeclareOption{065}{
\def\paperNumber{065}
}

\DeclareOption{65}{
\def\paperNumber{065}
}

\DeclareOption{066}{
\def\paperNumber{066}
}

\DeclareOption{66}{
\def\paperNumber{066}
}

\DeclareOption{067}{
\def\paperNumber{067}
}

\DeclareOption{67}{
\def\paperNumber{067}
}

\DeclareOption{068}{
\def\paperNumber{068}
}

\DeclareOption{68}{
\def\paperNumber{068}
}

\DeclareOption{069}{
\def\paperNumber{069}
}

\DeclareOption{69}{
\def\paperNumber{069}
}

\DeclareOption{070}{
\def\paperNumber{070}
}

\DeclareOption{70}{
\def\paperNumber{070}
}

\DeclareOption{071}{
\def\paperNumber{071}
}

\DeclareOption{71}{
\def\paperNumber{071}
}

\DeclareOption{072}{
\def\paperNumber{072}
}

\DeclareOption{72}{
\def\paperNumber{072}
}

\DeclareOption{073}{
\def\paperNumber{073}
}

\DeclareOption{73}{
\def\paperNumber{073}
}

\DeclareOption{074}{
\def\paperNumber{074}
}

\DeclareOption{74}{
\def\paperNumber{074}
}

\DeclareOption{075}{
\def\paperNumber{075}
}

\DeclareOption{75}{
\def\paperNumber{075}
}

\DeclareOption{076}{
\def\paperNumber{076}
}

\DeclareOption{76}{
\def\paperNumber{076}
}

\DeclareOption{077}{
\def\paperNumber{077}
}

\DeclareOption{77}{
\def\paperNumber{077}
}

\DeclareOption{078}{
\def\paperNumber{078}
}

\DeclareOption{78}{
\def\paperNumber{078}
}

\DeclareOption{079}{
\def\paperNumber{079}
}

\DeclareOption{79}{
\def\paperNumber{079}
}

\DeclareOption{080}{
\def\paperNumber{080}
}

\DeclareOption{80}{
\def\paperNumber{080}
}

\DeclareOption{081}{
\def\paperNumber{081}
}

\DeclareOption{81}{
\def\paperNumber{081}
}

\DeclareOption{082}{
\def\paperNumber{082}
}

\DeclareOption{82}{
\def\paperNumber{082}
}

\DeclareOption{083}{
\def\paperNumber{083}
}

\DeclareOption{83}{
\def\paperNumber{083}
}

\DeclareOption{084}{
\def\paperNumber{084}
}

\DeclareOption{84}{
\def\paperNumber{084}
}

\DeclareOption{085}{
\def\paperNumber{085}
}

\DeclareOption{85}{
\def\paperNumber{085}
}

\DeclareOption{086}{
\def\paperNumber{086}
}

\DeclareOption{86}{
\def\paperNumber{086}
}

\DeclareOption{087}{
\def\paperNumber{087}
}

\DeclareOption{87}{
\def\paperNumber{087}
}

\DeclareOption{088}{
\def\paperNumber{088}
}

\DeclareOption{88}{
\def\paperNumber{088}
}

\DeclareOption{089}{
\def\paperNumber{089}
}

\DeclareOption{89}{
\def\paperNumber{089}
}

\DeclareOption{090}{
\def\paperNumber{090}
}

\DeclareOption{90}{
\def\paperNumber{090}
}

\DeclareOption{091}{
\def\paperNumber{091}
}

\DeclareOption{91}{
\def\paperNumber{091}
}

\DeclareOption{092}{
\def\paperNumber{092}
}

\DeclareOption{92}{
\def\paperNumber{092}
}

\DeclareOption{093}{
\def\paperNumber{093}
}

\DeclareOption{93}{
\def\paperNumber{093}
}

\DeclareOption{094}{
\def\paperNumber{094}
}

\DeclareOption{94}{
\def\paperNumber{094}
}

\DeclareOption{095}{
\def\paperNumber{095}
}

\DeclareOption{95}{
\def\paperNumber{095}
}

\DeclareOption{096}{
\def\paperNumber{096}
}

\DeclareOption{96}{
\def\paperNumber{096}
}

\DeclareOption{097}{
\def\paperNumber{097}
}

\DeclareOption{97}{
\def\paperNumber{097}
}

\DeclareOption{098}{
\def\paperNumber{098}
}

\DeclareOption{98}{
\def\paperNumber{098}
}

\DeclareOption{099}{
\def\paperNumber{099}
}

\DeclareOption{99}{
\def\paperNumber{099}
}

\DeclareOption{100}{
\def\paperNumber{100}
}

% set up correct header based on publication
\DeclareOption{IJPHM}{%
\fancyhead[C]{\small{\textsc{International Journal of Prognostics and Health Management}}}%
\renewcommand{\headrulewidth}{0pt}%					% Remove head ruler
\fancyfoot[R]{{\small{\thepage}}}% --- footer all pages
\fancypagestyle{plain}{% --- first page header and footer content
   \fancyhead[C]{}% --- Clear first page header
   \fancyfoot[L]{\small{International Journal of Prognostics and Health Management, ISSN2153-2648, \publicationYear~\paperNumber}} % --- Write first page footer (Journal Only)
   }
}

\DeclareOption{IJPHM-TB}{%
\fancyhead[C]{\small{\textsc{Technical Brief}}}%
\renewcommand{\headrulewidth}{0pt}%					% Remove head ruler
\fancyfoot[R]{{\small{\thepage}}}% --- footer all pages
\fancypagestyle{plain}{% --- first page header and footer content
	\fancyhead[C]{}% --- Clear first page header
	\fancyfoot[L]{\small{International Journal of Prognostics and Health Management, ISSN2153-2648, \publicationYear~\paperNumber}}%	% --- Write first page footer (Journal Only)
	}
}

\DeclareOption{IJPHM-COMM}{%
\fancyhead[C]{\small{\textsc{Communication}}}%
\renewcommand{\headrulewidth}{0pt}%					% Remove head ruler
\fancyfoot[R]{{\small{\thepage}}}% --- footer all pages
\fancypagestyle{plain}{% --- first page header and footer content
	\fancyhead[C]{}% --- Clear first page header
	\fancyfoot[L]{\small{International Journal of Prognostics and Health Management, ISSN2153-2648, \publicationYear~\paperNumber}}%	% --- Write first page footer (Journal Only)
	}
}

\DeclareOption{PHME}{%
\fancyhead[C]{\small{\textsc{European Conference of the Prognostics and Health Management Society \publicationYear}}}% \the\year}}}%
\renewcommand{\headrulewidth}{0pt}%					% Remove head ruler
\fancyfoot[R]{{\small{\thepage}}}% --- footer all pages
\fancypagestyle{plain}{% --- first page header and footer content
   \fancyhead[C]{}}% --- Clear first page header
}

\DeclareOption{PHM}{%
\fancyhead[C]{\small{\textsc{Annual Conference of the Prognostics and Health Management Society \publicationYear}}}%
\renewcommand{\headrulewidth}{0pt}%					% Remove head ruler
\fancyfoot[R]{{\small{\thepage}}}% --- footer all pages
\fancypagestyle{plain}{% --- first page header and footer content
   \fancyhead[C]{}}% --- Clear first page header
}

\ProcessOptions\relax


%%%%%%%%\fancyhead[C]{\small{European Conference of the Prognostics and Health
%%%%%%%%   Management Society, 2012}}
%%%%%%%%\fancyhead[C]{\small{Annual Conference of the Prognostics and Health Management Society, 2012}}
%%%%%%%% \fancyhead[C]{\small{\textsc{Technical Brief}}}
 %%%%%%%\fancyhead[C]{\small{\textsc{International Journal of Prognostics and Health Management}}}
%%%%%%%
%%%%%%%\renewcommand{\headrulewidth}{0pt}					% Remove head ruler
%%%%%%%
%%%%%%%% --- footer all pages
%%%%%%%\fancyfoot[R]{{\small{\thepage}}}
%%%%%%%
%%%%%%%% --- first page header and footer content
%%%%%%%\fancypagestyle{plain}{
  %%%%%%%% --- Clear first page header
  %%%%%%%\fancyhead[C]{}
  %%%%%%%% --- Write first page footer (Journal Only)
  %%%%%%%% NO footer for conference
  %%%%%%%\fancyfoot[L]{\small{International Journal of Prognostics and Health Management, ISSN2153-2648, \the\year ***}}	
  %%%%%%%% [MD] what is the *** there for? isn't this something that users should enter via a command once they get paper number?
%%%%%%%
  %%%%%%%% --- Clear first page page number
  %%%%%%%%\fancyfoot[R]{\color{white}{\small{\thepage}}}
  %%%%%%%\fancyfoot[R]{}
%%%%%%%}
% END OF HEADER AND FOOTER CONTENT DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: FONT SIZE DECLARATIONS
%
% ------------------------------------------------------------------------------------------
% http://wiki.lyx.org/FAQ/ChangeFontUsingLatex
% http://xpt.sourceforge.net/techdocs/language/latex/latex32-LaTeXAndFonts/ar01s14.html
\def\@normalsize{\@setsize\normalsize{10pt}\xpt\@xpt}   		% 10 point on 11
\def\normalsize{\@setsize\normalsize{10pt}\xpt\@xpt}   		% 10 point on 11
\def\small{\@setsize\small{9pt}\ixpt\@ixpt}            			% 9 point on 10
\def\footnotesize{\@setsize\footnotesize{8pt}\viiipt\@viiipt} 	% 9 point on 10
\def\scriptsize{\@setsize\scriptsize{8pt}\viiipt\@viiipt} 		% 7 point on 8
\def\tiny{\@setsize\tiny{7pt}\viipt\@viipt}               			% 6 point on 7
\def\large{\@setsize\large{12pt}\xiipt\@xiipt}            			% 11 point on 12
\def\Large{\@setsize\Large{14pt}\xivpt\@xivpt}          		% 12 point on 14
\def\LARGE{\@setsize\LARGE{16pt}\xviipt\@xviipt}          		% 14 point on 16
\def\huge{\@setsize\huge{18pt}\xviiipt\@xviiipt}          		% 17 point on 20
\def\Huge{\@setsize\Huge{23pt}\xxiiipt\@xxiiipt}              		% 20 point on 23
\def\email{\@setsize\email{9pt}\ixpt\@ixpt}              			% 9 point
% TO DO:
% - This needs to be properly configured and documented. There might not be a need to do this.
% - Look at the article.cls class to identify how the sizes are defined. There should be a file size10.clo that will contain
%   the standard definitions.
% END of FONT SIZE DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: PARAGRAPH DECLARATIONS
%
% ------------------------------------------------------------------------------------------
% Linespacing
% NOTE: Use \linespread{1.3} for "one and a half" line spacing, and \linespread{1.6} for "double" line spacing.
\linespread{1.2}
% [MD] setspace package might be easier to use?

% Indentation
\setlength{\parindent}{0pt}

% Spacing between paragraphs
\setlength{\parskip}{6pt}

% NOTES
% - \parskip will affect lists too. This needs to be fixed later on the lists environments
% END of PARAGRAPH DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: TITLE BLOCK DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\def\@maketitle{%
	\def\and{\unskip{, }}
  	\def\And{\unskip{, and }}
	\vskip 0.55in 										% Space before title is 0.5"
	\begin{center}
		{\LARGE\bf\@title\par}					% Title text
		%
		\vskip 14pt											% Space after title, 14pt
		%
		{\normalsize \@author \par}			% Author text			
		%
		\vskip 0.02in										% Space after authors, 12pt
		%
		{\normalsize\it									% Affiliation
		\vskip -1pt
		\begin{tabular}[t]{c}				
			\address
		\end{tabular}
		\par}
		%
		\vskip 26pt											% Space after affiliation, 24 + 3 pt
		%
	\end{center}
} % end maketitle definition

% END of TITLE BLOCK DECLARATIONS

% ------------------------------------------------------------------------------------------
%
%: ABSTRACT ENVIRONMENT DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\renewenvironment{abstract}{\centerline{\normalsize\bfseries\scshape Abstract}\vspace{0pt}\noindent\normalsize}
% NOTE
% - No need to remove vspace because the \parskip variable is set to 6pt. If this variable is changed, then this needs to be updated.
% END of ABSTRACT ENVIRONMENT DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: LICENSE FOOTNOTE DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\newcommand{\phmLicenseFootnote}[1]{%
\insert\footins{\noindent\footnotesize{#1~et al. This is an open-access article distributed under the terms of 			the Creative Commons Attribution 3.0 United States License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.}}
}
% TO DO:
% - Make use of a variable for the first name. This way the author will have to provide it only once
% END of LICENSE FOOTNOTE DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: AFFILIATIONS DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\newcommand{\authorNumber}[1]{\textnormal{\textsuperscript{#1}}}	 	% This command is for formatting the author 
														% number as a subscript
\newcommand{\affiliation}[3]{\\ \authorNumber{#1} #2 \\ #3}
\newcommand{\address}[1]{\def\address{#1}}

% TO DO:
% - Consider changing the structure of this so authors cannot mess up layout of affiliation section
%END of AFFILIATIONS DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: SECTIONS DECLARATIONS
%
% ------------------------------------------------------------------------------------------

% Section font style and before/after spacing   
\def\section{\@startsection{section}{1}{\z@}{6pt}{0.01pt}{\normalsize\bf\scshape}}
\def\subsection{\@startsection{subsection}{2}{\z@}{6pt}{0.01pt}{\normalsize\bf}}
\def\subsubsection{\@startsection{subsubsection}{3}{\z@}{6pt}{0.01pt}{\normalsize\bf}}

% NOTE: Argument for definition as stated on the IEEE templates. Not sure if correct.
% arguments are: #1 - sectiontype name
% (for \@sect)   #2 - section level
%                #3 - section heading indent
%                #4 - top separation (absolute value used, neg indicates not to indent main text)
%                     If negative, make stretch parts negative too!
%                #5 - (absolute value used) positive: bottom separation after heading,
%                      negative: amount to indent main text after heading
%                Both #4 and #5 negative means to indent main text and use negative top separation
%                #6 - font control
% You've got to have \normalfont\normalsize in the font specs below to prevent

% \@startsection {NAME}{LEVEL}{INDENT}{BEFORESKIP}{AFTERSKIP}{STYLE} 
%            optional * [ALTHEADING]{HEADING}
%    Generic command to start a section.  
%    NAME       : e.g., 'subsection'
%    LEVEL      : a number, denoting depth of section -- e.g., chapter=1,
%                 section = 2, etc.  A section number will be printed if
%                 and only if LEVEL < or = the value of the secnumdepth
%                 counter.
%    INDENT     : Indentation of heading from left margin
%    BEFORESKIP : Absolute value = skip to leave above the heading.  
%                 If negative, then paragraph indent of text following 
%                 heading is suppressed.
%    AFTERSKIP  : if positive, then skip to leave below heading,
%                       else - skip to leave to right of run-in heading.
%    STYLE      : commands to set style
%  If '*' missing, then increments the counter.  If it is present, then
%  there should be no [ALTHEADING] argument.  A sectioning command
%  is normally defined to \@startsection + its first six arguments.
%
% \z@ is shorthand for 0pt indentation from left margin


% Define section numbering styles
\def\thesection{\arabic{section}}
\def\thesubsection{\thesection.\arabic{subsection}}
\def\thesubsubsection{\thesubsection.\arabic{subsubsection}}

%% Singlespace References
\newcommand{\PHMbibliography}[1]{\begin{singlespace}\bibliography{#1}\end{singlespace}}

% Update section formatting to include period after the section number
% to match MS word style
\renewcommand*{\@seccntformat}[1]{
       \csname the#1\endcsname.
}
% the "\csname the#1\endcsname" part puts in the section number, then the 
% "." there puts in the ".", and then the "\quad" inserts some space. 
% There is a description here:
% http://www.tex.ac.uk/cgi-bin/texfaq2html?label=seccntfmt

% NOTES on Latex sections
% http://help-csli.stanford.edu/tex/latex-sections.shtml
% END of SECTIONS DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: FOOTNOTES DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\footnotesep 6.65pt \skip\footins 9pt plus 4pt minus 2pt
\def\footnoterule{\kern-3pt \hrule width 5pc \kern 2.6pt }
\setcounter{footnote}{0}
% NOTE:
% TO DO:
% - Not sure if these declarations are actually needed
% END of FOOTNOTES DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: ILLUSTRATIONS DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\floatsep 12pt plus 2pt minus 2pt
\textfloatsep 16pt plus 2pt minus 4pt
\intextsep 12pt plus 2pt minus 2pt
\dblfloatsep 12pt plus 2pt minus 2pt
\dbltextfloatsep 18pt plus 2pt minus 4pt
% NOTE:
% TO DO:
% - Not sure if these declarations are actually needed
% END of ILLUSTRATIONS DECLARATIONS


% ------------------------------------------------------------------------------------------
%
%: DISPLAYS DECLARATIONS
%
% ------------------------------------------------------------------------------------------
\abovedisplayskip 7pt plus2pt minus5pt%
\belowdisplayskip \abovedisplayskip
\abovedisplayshortskip  0pt plus3pt%   
\belowdisplayshortskip  4pt plus3pt minus3pt%
% END of DISPLAYS DECLARATIONS



% ------------------------------------------------------------------------------------------
%
%: LISTS DECLARATIONS
%
% ------------------------------------------------------------------------------------------
% Indentation for all the lists and sublists. Applies to enumerate, itemize
\leftmargini 0.25in				% This should be 0.25in which is the column separation size
\leftmarginii 2em
\leftmarginiii 1em 
\leftmarginiv 0.5em
\leftmarginv 0.5em 
\leftmarginvi 0.5em

% Applies to enumerate, itemize and description
\leftmargin\leftmargini							% ???
\labelsep 10pt									% separation from label to text (update w/MSWord dim.)
\labelwidth\leftmargini\advance\labelwidth-\labelsep


% Applies to enumerate, itemize and description
\def\@listI{\leftmargin\leftmargini 
\parsep 0pt plus 1pt minus 0.5pt%					% This is the element to element separation
\topsep 0pt plus 1pt minus 2pt%					% this is the top separation
\itemsep 3pt plus 1pt minus 0.5pt%					% This is the element to element separation (repeated)
\partopsep 6pt plus 0.5pt minus 0.5pt}				% bottom separation

\let\@listi\@listI					% ??
\@listi 						% ??

\def\@listii{\leftmargin\leftmarginii
   \labelwidth\leftmarginii\advance\labelwidth-\labelsep
   \parsep 1pt plus 0.5pt minus 0.5pt
   \topsep 2pt plus 1pt minus 0.5pt
   \itemsep \parsep}
\def\@listiii{\leftmargin\leftmarginiii
    \labelwidth\leftmarginiii\advance\labelwidth-\labelsep
    \parsep 0pt plus 1pt
    \partopsep 0.5pt plus 0pt minus 0.5pt
    \topsep 1pt plus 0.5pt minus 0.5pt 
    \itemsep \topsep}
\def\@listiv{\leftmargin\leftmarginiv
     \labelwidth\leftmarginiv\advance\labelwidth-\labelsep}
\def\@listv{\leftmargin\leftmarginv
     \labelwidth\leftmarginv\advance\labelwidth-\labelsep}
\def\@listvi{\leftmargin\leftmarginvi
     \labelwidth\leftmarginvi\advance\labelwidth-\labelsep}
% NOTE:
% TO DO:
% - This section needs to be properly understood. Embedded lists needing indented numbering have not been tested.     
% END of LISTS DECLARATIONS



