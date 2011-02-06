#!/usr/local/gauche/bin/gosh
;#!/usr/local/gauche/bin/speedygosh

;;; 名前の由来:
;;; 古き良き google deskbar のショートカットキーがctrl + alt + G であり、
;;; google deskbar なき後に mayu および yamy の設定ファイルに
;;; このショートカットキーを定義する際の設定が「C-A-G」であった事に由来する。

;; TODO: html部をローカル保存しても動くように、formのactionを絶対指定する
;; TODO: 簡易履歴機能(というか、ストレージ機能)をつける
;; TODO: 簡易eval機能をつける？
;; TODO: 最終的には、自己組織化可能にする？

(define-module c-a-g_cgi
  (use www.cgi)
  (use rfc.http)
  (use text.html-lite)
  (use text.tree)
  (use srfi-1)
  (use srfi-13)
  (use rfc.uri)
  (use rfc.cookie)
  (use util.list)
  (export
    ))
(select-module c-a-g_cgi)

(define-macro (hoge . args)
  '(...))

(define (main args)
  (set! (port-buffering (current-error-port)) :line)
  (cgi-main
    (lambda (params)
      (emit-content params))
    :on-error (lambda (e)
                (list
                  (cgi-header)
                  (html:pre
                    (html-escape-string
                      (call-with-output-string
                        (cut with-error-to-port <> (cut report-error e))))))))
  0)


(define (emit-content params)
  (let1 c (make-keyword (cgi-get-parameter "c" params :default ""))
    (case c
      ((:s) (emit-content-solve params))
      (else (emit-content-form params)))))


(define (emit-content-form params)
  (let ((query (cgi-get-parameter "q" params :default "")))
    (list
      (cgi-header :content-type "text/html; charset=utf-8"
                  :pragma "no-cache"
                  :cache-control "no-cache"
                  )
      (html:html
        (html:head
          (html:title "g.cgi")
          ;(html:script :src "/chaton/prototype.js" :type "text/javascript")
          )
        (html:body :id "the-body"
                   (the-form query)
                   )))))

(define (javascript . scripts)
  (html:script
    :type "text/javascript"
    (intersperse
      "\n"
      `("<!--"
        ,@scripts
        "// -->"))))

(define (the-form query)
  (html:form
    ;:action (cgi-get-metavariable "REQUEST_URI")
    :method "get"
    :target "_self"
    :name "send"
    (html:div
      (html:input :type "hidden" :name "c" :value "s")
      (html:textarea :name "q" :id "post-q"
                     :rows "3" :cols "40"
                     :onkeydown "if (event.keyCode == 13) { self.document.send.submit() }"
                     (html-escape-string query))
      (html:input :type "submit" ;:name "submit"
                  :id "post-submit" :value "解決")
      )
    (javascript "self.document.send.q.focus();")
    ;; TODO: 説明等を追加してもよい
    ))

(define (dispatch-w-nl goto-url query)
  ;; 今のところ、vimircのコピペのみ対応
  ;; 対応する必要があるのは、以下のような、一行80文字までの、改行区切りの文字列
  ;; (例1:vimircのシングルモード)
  ;;  [1]irc.server-name.|01:48 <nick>: あいうえおかきくけこさしすせ htt|@nick2
  ;; *[3]#channnel       |      p://www.google.com/ そたちつてとなにぬね|~
  ;; ~                   |      のはひふへほ                            |~
  ;; (例2:)
  ;;
  (let/cc return
    (let1 goto-url (make-goto-url return)
      #f)))

(define (dispatch-w-cmd goto-url cmd query)
  (let/cc return
    (let1 goto-url (make-goto-url return)
      ;; TODO: 対応可能コマンドはマクロで定義できるようにする事
      ;; TODO: あとで
      #f)))

(define *re:scheme*
  ;; http:// ttp:// tp://
  ;; (match 1) => https の "s" もしくは ""
  #/^(?:http|ttp|tp)(s?)\:\/\//)
(define *re:userpass*
  ;; 空、もしくは user@ もしくは user:pass@ 
  ;; TODO: 使用可能文字増やすべきかも
  #/^(?:|(?:[\w\%]+(?:[\w\%]+)?\@))/)
(define *re:domain*
  ;; domain.name:80
  #/^[\w\-]+(?:\.[\w\-]+)*(?:\:\d+)?/)
(define *re:rest*
  ;; 空、もしくは /... もしくは /...#...
  ;; fragment部にマルチバイト文字を許容するかどうかは微妙
  ;; TODO: ↓もう少しちゃんとする事
  #/^(?:|(?:\/[\!\#\$\%\&\'\(\)\*\+\,\-\.\/0-9\:\;\=\?\@A-Z\_a-z\~]+))$/)
(define *re:url*
  #/https?\:\/\/[\!\#\$\%\&\'\(\)\*\+\,\-\.\/0-9\:\;\=\?\@A-Z\_a-z\~]+/)

(define (dispatch-uri goto-url query)
  ;; uriとみなす為の判定に必要な部分は、以下の通り
  ;; - scheme部( http:// https:// ttp:// tp:// )。なくてもokだが要補完
  ;; - userpass部( user:pass@ )。なくてもok
  ;; - domain部( host.name )。必須
  ;; - rest部( /path/to/doc.html )。なくてもok
  ;; 尚、domain部以外は必須ではないが、完全にdomain部しか存在しない場合、
  ;; それはuriでない可能性が高い為、例外的にuriではない扱いとする
  (and-let* (
             ;; まず、whitespaceの除去を行う
             (query-wo-ws (regexp-replace-all #/\s/ query ""))
             ;; 各マッチを取得する(#fが出たら終了)
             (match-scheme (or
                             (*re:scheme* query-wo-ws) ; schemeあり
                             (#/^()/ query-wo-ws))) ; schemeなし
             (match-userpass (*re:userpass* (match-scheme 'after)))
             (match-domain (*re:domain* (match-userpass 'after)))
             (match-rest (*re:rest* (match-domain 'after)))
             (_ (not ; domain部しか存在しないなら、uri扱いしない
                  (and
                    (string=? "" (match-scheme))
                    (string=? "" (match-rest)))))
             (url (string-append
                    ;; scheme
                    (if (string=? "" (match-scheme))
                      "http://"
                      (string-append "http" (match-scheme 1) "://"))
                    ;; userpass
                    (match-userpass)
                    ;; domain
                    (match-domain)
                    ;; rest
                    (match-rest))))
    ;; TODO: referer消し
    ;;       - どのように実現する？
    ;;       -- googleのリダイレクタを使う(面倒)
    ;;       -- JavaScriptでリダイレクト(可能かどうか不明)
    (goto-url url)))

(define (make-goto-url return)
  (define (goto-url url)
    (return
      (cgi-header
        :pragma "no-cache"
        :cache-control "no-cache"
        :location url)))
  goto-url)

(define (emit-content-solve params)
  (let/cc return
    (let1 goto-url (make-goto-url return)
      ;; TODO: goto-urlを直に渡すのではなく、手続きの返り値がurlか#fかで
      ;;       分岐させるようにした方がいい
      (let* ((query (cgi-get-parameter "q" params :default ""))
             (_ (when (string=? "" query) (goto-url (self-url))))
             ;; まず、改行が意味を持つ分岐を先に処理
             (_ (dispatch-w-nl goto-url query))
             ;; queryの先頭にコマンド指定がされているなら、先にそれを取り出す
             ;; コマンド文字列は、1〜3文字のasciiとする
             (m (#/^([\w\%\!\@\.\:\/\*\+\-]{1,3})\s+/ query))
             (cmd (and m (string-downcase (m 1))))
             (query-wo-cmd (if m (m 'after) query))
             ;; 改行を除去する
             (query-wo-nl (regexp-replace-all #/\n|\r/ query-wo-cmd " "))
             (_ (when (string=? "" query-wo-nl) (goto-url (self-url))))
             ;; コマンドを処理
             (_ (dispatch-w-cmd goto-url cmd query-wo-nl))
             ;; 内容がuriっぽかったら、uriとして処理を行う
             (_ (dispatch-uri goto-url query-wo-nl))
             )
        ;; どれにもマッチしなかった。google検索する
        (goto-url
          (append-params-to-url
            "http://www.google.com/search"
            `(("q" ,query-wo-nl))))))))


(define (append-params-to-url url params)
  (if (null? params)
    url
    (receive (url-without-fragment fragment) (let1 m (#/(\#.*)/ url)
                                               (if m
                                                 (values (m 'before) (m 1))
                                                 (values url "")))
      (call-with-output-string
        (lambda (p)
          (letrec ((delimitee (if (#/\?/ url-without-fragment)
                                (lambda () "&")
                                (lambda ()
                                  (set! delimitee (lambda () "&"))
                                  "?"))))
            (display url-without-fragment p)
            (let loop ((left-params params))
              (if (null? left-params)
                (display fragment p)
                (let ((key-encoded (uri-encode-string (caar left-params)))
                      (vals (cdar left-params))
                      (next-left (cdr left-params))
                      )
                  (if (pair? vals)
                    (for-each
                      (lambda (val)
                        (display (delimitee) p) ; "?" or "&"
                        (display key-encoded p)
                        (display "=" p)
                        (display (uri-encode-string (if (string? val) val "")) p))
                      vals)
                    (begin
                      (display (delimitee) p)
                      (display key-encoded p)))
                  (loop next-left))))))))))

(define (completion-uri uri server-name server-port https)
  (receive (uri-scheme
            uri-userinfo
            uri-hostname
            uri-port
            uri-path
            uri-query
            uri-fragment) (uri-parse uri)
    ;; uri-schemeが無い時にだけ補完する
    ;; 但し、server-nameが与えられていない場合は補完できないので、何もしない
    (if (or uri-scheme (not server-name))
      uri
      (let* ((scheme (if https "https" "http"))
             (default-port (if https 443 80))
             )
        (uri-compose
          :scheme scheme
          :userinfo uri-userinfo
          :host server-name
          :port (and
                  server-port
                  (not (eqv? default-port (x->number server-port)))
                  server-port)
          :path uri-path
          :query uri-query
          :fragment uri-fragment)))))

(define (path->url path)
  (if (#/^\// path)
    (completion-uri
      path
      (cgi-get-metavariable "SERVER_NAME")
      (cgi-get-metavariable "SERVER_PORT")
      (cgi-get-metavariable "HTTPS"))
    path))

(define (self-url)
  (path->url (self-path)))

(define (self-url/path-info)
  (path->url (self-path/path-info)))

(define (self-url/slash)
  (string-append (self-url) "/"))

(define (self-path)
  (or (cgi-get-metavariable "SCRIPT_NAME") "/"))

(define (self-path/path-info)
  ;; note: PATH_INFOは既にデコードされてしまっているので使わない事
  (let* ((r (or (cgi-get-metavariable "REQUEST_URI") "/"))
         (m (#/\?/ r))
         )
    (if m
      (m 'before)
      r)))

(define (self-path/slash)
  (string-append (self-path) "/"))

;;;===================================================================

(select-module user)
(define main (with-module c-a-g_cgi main))

;; Local variables:
;; mode: scheme
;; end:
;; vim: set ft=scheme: