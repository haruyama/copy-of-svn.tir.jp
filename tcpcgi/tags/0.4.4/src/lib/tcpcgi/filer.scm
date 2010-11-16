;;; coding: euc-jp
;;; -*- scheme -*-
;;; vim:set ft=scheme ts=8 sts=2 sw=2 et:
;;; $Id$

;;; ToDo : より良いインターフェースを考える事

;;; ToDo : HTTP/1.1コンプリート
;;; ToDo : HTTP/1.1どこまで実装したか、どの順で実装するかの表を作る事

;;; ToDo : Rangeヘッダのサポート
;;; ToDo : HEADのサポートと、許可されたmethod以外は405, 501を返すようにする事
;;; ToDo : OPTIONS, TRACE等のサポート
;;;        http://www.studyinghttp.net/method

;;; ToDo : apacheのmime.types形式のファイルをパーズして使うようにする？

;;; note : 現在のmime-type判別は、pathの拡張子ではなく、実体の拡張子を見ます






(define-module tcpcgi.filer
  (use srfi-2) ; and-let*
  (use srfi-13) ; string-prefix?
  (use file.util)
  (use text.tree)
  (use text.html-lite)
  (use www.cgi)

  (use tcpcgi.errordoc)
  (export
    <tcpcgi.filer>
    make-filer-thunk
    *mime-table*
    ))
(select-module tcpcgi.filer)


(define-class <tcpcgi.filer> ()
  (
   (root-path :accessor root-path-of
              :init-keyword :root-path
              :init-value #f)
   (error-proc :accessor error-proc-of
               :init-keyword :error-proc
               :init-value #f)
   (auto-index :accessor auto-index-of
               :init-keyword :auto-index
               :init-value #f)
   (auth :accessor auth-of
         :init-keyword :auth
         :init-value #f)
   ))


(define (path-include-dotfile? path)
  (#/\/\./ path))


;; cgi-thunk
(define (execute-filer self)
  (let* ((root-path (root-path-of self))
         (path-info (or
                      (cgi-get-metavariable "PATH_INFO")
                      "")) ; path-infoは/はじまり
         (target-path (simplify-path
                        (string-append root-path path-info)))
         (error-proc (error-proc-of self))
         (basename (sys-basename target-path))
         (ext (and-let* ((m (#/\.([^\.]+)$/ basename)))
                (m 1)))
         )
    (cond
      ((not (file-exists? target-path)) (error-proc 404))
      ((file-is-directory? target-path) (error-proc 403))
      ((not (file-is-readable? target-path)) (error-proc 403))
      ((not (string-prefix? root-path target-path)) (error-proc 403))
      ((path-include-dotfile? target-path) (error-proc 403))
      (else
        (write-tree
          (apply cgi-header
            :content-type (or
                            (and
                              ext
                              (ref *mime-table* ext #f))
                            *fallback-mime-type*)
            (or
              (and-let* ((response-code
                           (cgi-get-metavariable "X_RESPONSE_CODE"))
                         (response-message
                           (status-code->label response-message))
                         )
                (list :status (format "~a ~a" response-code response-message)))
              '())))
        (copy-port
          (open-input-file target-path)
          (current-output-port))))))



;; cgi-thunkを返す。
(define (make-filer-thunk path . keywords)
  (let* ((root-path (sys-normalize-pathname
                      path
                      :absolute #t
                      :expand #t
                      :canonicalize #t))
         (filer (apply
                  make <tcpcgi.filer>
                  :root-path root-path
                  keywords))
         )
    (lambda ()
      (execute-filer filer))))


;(define-method hoge ((self <tcpcgi.filer>))
;  #f)



;; ToDo : あとで、参考にする事
;;        http://www.sakura.ad.jp/support/web/manual/tech/mime-types/
(define *fallback-mime-type* "text/plain")
;; 拡張子->mime-type
(define *mime-table*
  (hash-table
    'string=?
    ;; text
    '("css"     . "text/css")
    '("html"    . "text/html")
    '("htm"     . "text/html")
    '("shtml"   . "text/html")
    '("xhtml"   . "application/xhtml+xml")
    '("dtd"     . "application/xml-dtd")
    '("asc"     . "text/plain")
    '("txt"     . "text/plain")
    '("rtx"     . "text/richtext")
    '("rtf"     . "text/rtf")
    '("sgml"    . "text/sgml")
    '("tsv"     . "text/tab-separated-values")
    ;; other document
    '("mathml"  . "application/mathml+xml")
    '("doc"     . "application/msword")
    '("pdf"     . "application/pdf")
    '("eps"     . "application/postscript")
    '("ps"      . "application/postscript")
    '("rdf"     . "application/rdf+xml")
    '("xls"     . "application/vnd.ms-excel")
    '("ppt"     . "application/vnd.ms-powerpoint")
    '("dvi"     . "application/x-dvi")
    '("latex"   . "application/x-latex")
    '("tex"     . "application/x-tex")
    '("texi"    . "application/x-texinfo")
    '("tr"      . "application/x-troff")
    '("roff"    . "application/x-troff")
    '("man"     . "application/x-troff-man")
    '("xml"     . "application/xml")
    '("xsl"     . "application/xml")
    ;; archive
    '("gz"      . "application/octet-stream")
    '("bz2"     . "application/octet-stream")
    '("tar"     . "application/octet-stream")
    '("zip"     . "application/octet-stream")
    '("tgz"     . "application/octet-stream")
    '("tbz"     . "application/octet-stream")
    '("hqx"     . "application/mac-binhex40")
    '("lzh"     . "application/octet-stream")
    '("sit"     . "application/x-stuffit")
    ;; program text
    '("xul"     . "application/vnd.mozilla.xul+xml")
    '("js"      . "application/x-javascript")
    '("xslt"    . "application/xslt+xml")
    ;; program binary
    '("bin"     . "application/octet-stream")
    '("exe"     . "application/octet-stream")
    '("com"     . "application/octet-stream")
    '("class"   . "application/octet-stream")
    '("so"      . "application/octet-stream")
    '("dll"     . "application/octet-stream")
    '("swf"     . "application/x-shockwave-flash")
    ;; image
    '("bmp"     . "image/bmp")
    '("gif"     . "image/gif")
    '("jpeg"    . "image/jpeg")
    '("jpg"     . "image/jpeg")
    '("png"     . "image/png")
    '("svg"     . "image/svg+xml")
    '("tiff"    . "image/tiff")
    '("ico"     . "image/x-icon")
    '("pnm"     . "image/x-portable-anymap")
    '("pbm"     . "image/x-portable-bitmap")
    '("pgm"     . "image/x-portable-graymap")
    '("ppm"     . "image/x-portable-pixmap")
    '("rgb"     . "image/x-rgb")
    '("xbm"     . "image/x-xbitmap")
    '("xpm"     . "image/x-xpixmap")
    '("xwd"     . "image/x-xwindowdump")
    ;; sound
    '("ogg"     . "application/ogg")
    '("au"      . "audio/basic")
    '("snd"     . "audio/basic")
    '("mid"     . "audio/midi")
    '("midi"    . "audio/midi")
    '("kar"     . "audio/midi")
    '("mpga"    . "audio/mpeg")
    '("mp2"     . "audio/mpeg")
    '("mp3"     . "audio/mpeg")
    '("aif"     . "audio/x-aiff")
    '("aiff"    . "audio/x-aiff")
    '("aifc"    . "audio/x-aiff")
    '("m3u"     . "audio/x-mpegurl")
    '("ram"     . "audio/x-pn-realaudio")
    '("rm"      . "audio/x-pn-realaudio")
    '("ra"      . "audio/x-realaudio")
    '("wav"     . "audio/x-wav")
    '("pls"     . "audio/x-scpls")
    ;; video
    '("mpeg"    . "video/mpeg")
    '("mpg"     . "video/mpeg")
    '("mpe"     . "video/mpeg")
    '("qt"      . "video/quicktime")
    '("mov"     . "video/quicktime")
    '("mxu"     . "video/vnd.mpegurl")
    '("avi"     . "video/x-msvideo")
    ;; other
    '("wrl"     . "model/vrml")
    '("vrml"    . "model/vrml")
    ;; x509
    '("crt"     . "application/pkix-cert")
    '("crl"     . "application/pkix-crl")
    ))


(provide "tcpcgi/filer")

