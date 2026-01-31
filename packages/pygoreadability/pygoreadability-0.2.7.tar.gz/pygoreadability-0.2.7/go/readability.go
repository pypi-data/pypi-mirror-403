package main

/*
#include <stdlib.h>

typedef struct {
    char* title;
    int title_len;
    char* byline;
    int byline_len;
    char* excerpt;
    int excerpt_len;
    char* site_name;
    int site_name_len;
    char* image_url;
    int image_url_len;
    char* favicon;
    int favicon_len;
    char* language;
    int language_len;
    char* published_time;
    int published_time_len;
    char* modified_time;
    int modified_time_len;
    char* content_html;
    int content_html_len;
    char* content_text;
    int content_text_len;
    char* error;
    int error_len;
} ReadabilityArticle;
*/
import "C"

import (
    "bytes"
    "net/url"
    "strings"
    "time"
    "unsafe"

    readability "codeberg.org/readeck/go-readability/v2"
)

//export FromString
func FromString(html *C.char, htmlLen C.int, pageURL *C.char, urlLen C.int) *C.ReadabilityArticle {
    if html == nil || htmlLen <= 0 {
        return newError("html input is nil")
    }

    input := C.GoStringN(html, htmlLen)
    var parsedURL *url.URL
    if pageURL != nil && urlLen > 0 {
        rawURL := C.GoStringN(pageURL, urlLen)
        if rawURL != "" {
            u, err := url.Parse(rawURL)
            if err != nil {
                return newError("failed to parse url: " + err.Error())
            }
            parsedURL = u
        }
    }

    article, err := readability.FromReader(strings.NewReader(input), parsedURL)
    if err != nil {
        return newError(err.Error())
    }

    contentHTML, renderErr := renderHTML(&article)
    if renderErr != nil {
        return newError(renderErr.Error())
    }
    contentText, renderErr := renderText(&article)
    if renderErr != nil {
        return newError(renderErr.Error())
    }

    published, err := formatTime(article.PublishedTime())
    if err != nil {
        return newError(err.Error())
    }
    modified, err := formatTime(article.ModifiedTime())
    if err != nil {
        return newError(err.Error())
    }

    return newArticle(
        article.Title(),
        article.Byline(),
        article.Excerpt(),
        article.SiteName(),
        article.ImageURL(),
        article.Favicon(),
        article.Language(),
        published,
        modified,
        contentHTML,
        contentText,
        "",
    )
}

func formatTime(t time.Time, err error) (string, error) {
    if err == readability.ErrTimestampMissing {
        return "", nil
    }
    if err != nil {
        return "", err
    }
    return t.UTC().Format(time.RFC3339), nil
}

func renderHTML(article *readability.Article) (string, error) {
    if article.Node == nil {
        return "", nil
    }
    var buf bytes.Buffer
    if err := article.RenderHTML(&buf); err != nil {
        return "", err
    }
    return buf.String(), nil
}

func renderText(article *readability.Article) (string, error) {
    if article.Node == nil {
        return "", nil
    }
    var buf bytes.Buffer
    if err := article.RenderText(&buf); err != nil {
        return "", err
    }
    return buf.String(), nil
}

func newArticle(
    title string,
    byline string,
    excerpt string,
    siteName string,
    imageURL string,
    favicon string,
    language string,
    publishedTime string,
    modifiedTime string,
    contentHTML string,
    contentText string,
    err string,
) *C.ReadabilityArticle {
    article := (*C.ReadabilityArticle)(C.malloc(C.size_t(unsafe.Sizeof(C.ReadabilityArticle{}))))
    if article == nil {
        return nil
    }
    article.title, article.title_len = toCString(title)
    article.byline, article.byline_len = toCString(byline)
    article.excerpt, article.excerpt_len = toCString(excerpt)
    article.site_name, article.site_name_len = toCString(siteName)
    article.image_url, article.image_url_len = toCString(imageURL)
    article.favicon, article.favicon_len = toCString(favicon)
    article.language, article.language_len = toCString(language)
    article.published_time, article.published_time_len = toCString(publishedTime)
    article.modified_time, article.modified_time_len = toCString(modifiedTime)
    article.content_html, article.content_html_len = toCString(contentHTML)
    article.content_text, article.content_text_len = toCString(contentText)
    article.error, article.error_len = toCString(err)
    return article
}

func newError(msg string) *C.ReadabilityArticle {
    return newArticle("", "", "", "", "", "", "", "", "", "", "", msg)
}

func toCString(value string) (*C.char, C.int) {
    if value == "" {
        return nil, 0
    }
    buf := []byte(value)
    ptr := C.CBytes(buf)
    return (*C.char)(ptr), C.int(len(buf))
}

//export FreeArticle
func FreeArticle(article *C.ReadabilityArticle) {
    if article == nil {
        return
    }
    C.free(unsafe.Pointer(article.title))
    C.free(unsafe.Pointer(article.byline))
    C.free(unsafe.Pointer(article.excerpt))
    C.free(unsafe.Pointer(article.site_name))
    C.free(unsafe.Pointer(article.image_url))
    C.free(unsafe.Pointer(article.favicon))
    C.free(unsafe.Pointer(article.language))
    C.free(unsafe.Pointer(article.published_time))
    C.free(unsafe.Pointer(article.modified_time))
    C.free(unsafe.Pointer(article.content_html))
    C.free(unsafe.Pointer(article.content_text))
    C.free(unsafe.Pointer(article.error))
    C.free(unsafe.Pointer(article))
}

func main() {}
