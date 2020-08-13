Using cookies with PyIDM:

reference: https://github.com/ytdl-org/youtube-dl#how-do-i-pass-cookies-to-youtube-dl

Passing cookies to PyIDM is a good way to work around CAPTCHA, some websites require you to solve in particular 
cases in order to get access (e.g. YouTube, CloudFlare). 

you need to extract cookie file from your browser save it some where (for example: cookies.txt) then goto
Settings > Network > then check Use Cookies option
browse to select your cookies file ... done.

![cookies screenshot](https://user-images.githubusercontent.com/58998813/90165536-16c58680-dd99-11ea-99a8-edaec07246e5.png)

In order to extract cookies from browser use any conforming browser extension for exporting cookies. 
For example, [cookies.txt](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg) (for Chrome) 
or [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) (for Firefox) 

Note that the cookies file must be in Mozilla/Netscape format and the first line of the cookies file must be either 
`# HTTP Cookie File or # Netscape HTTP Cookie File`. 
Make sure you have correct newline format in the cookies file and convert newlines if necessary to correspond with your OS, 
namely CRLF (\r\n) for Windows and LF (\n) for Unix and Unix-like systems (Linux, macOS, etc.). 
HTTP Error 400: Bad Request when using cookies is a good sign of invalid newline format.




