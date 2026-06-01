# md-gui# MarkItDown GUI

যেকোনো ফাইল Markdown-এ convert করার সহজ desktop app।

---

## ইন্সটল (একবারই করতে হবে)

CMD খুলে এই দুটো command দাও:

```
pip install "markitdown[all]"
pip install tkinterdnd2
```

---

## চালানোর নিয়ম

`markitdown_gui.py` ফাইলের উপর **right-click → Open with → Python**

অথবা CMD-এ:

```
python markitdown_gui.py
```

---

## ব্যবহারের নিয়ম

1. ফাইল **drag & drop** করো অথবা **"ফাইল বেছে নাও"** বাটন চাপো
2. **"Convert করো"** বাটন চাপো
3. ডান পাশে Markdown আউটপুট দেখা যাবে
4. **কপি** করো অথবা `.md` ফাইল হিসেবে **সেভ** করো

---

## সাপোর্টেড ফাইল ফরম্যাট

| ফরম্যাট | এক্সটেনশন |
|--------|-----------|
| PDF | .pdf |
| Word | .docx, .doc |
| PowerPoint | .pptx, .ppt |
| Excel | .xlsx, .xls |
| CSV | .csv |
| JSON | .json |
| XML | .xml |
| HTML | .html, .htm |
| Text | .txt, .md |
| eBook | .epub |
| ZIP | .zip |
| Images | .jpg, .jpeg, .png, .gif, .webp |

---

## Requirements

- Python 3.10 বা তার উপরে
- markitdown[all]
- tkinterdnd2
