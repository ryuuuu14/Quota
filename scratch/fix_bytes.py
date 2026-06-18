with open('f:/annd/Quota/src/pages/4_CaiDatHeThong.py', 'rb') as f:
    content_bytes = f.read()

# Fix the corruption
bad_bytes = b'st.error("L\xe1\xbb\x97i: D\xe1\xbb    st.markdown'
good_bytes = b'st.error("L\xe1\xbb\x97i: D\xe1\xbb\xaf li\xe1\xbb\x87u b\xe1\xbb\x8b tr\xc3\xb9ng l\xe1\xba\xb7p ho\xe1\xba\xb7c kh\xc3\xb4ng h\xe1\xbb\xa3p l\xe1\xbb\x87.")\r\n                    except Exception as e:\r\n                        conn.rollback()\r\n                        st.error(f"L\xe1\xbb\x97i: {e}")\r\n    st.markdown(f\'<hr style="border-color: var(--md-outline-variant); margin: 24px 0;">\', unsafe_allow_html=True)\r\n    st.markdown'

if bad_bytes in content_bytes:
    content_bytes = content_bytes.replace(bad_bytes, good_bytes)
    with open('f:/annd/Quota/src/pages/4_CaiDatHeThong.py', 'wb') as f:
        f.write(content_bytes)
    print('Corruption fixed!')
else:
    print('Corruption not found!')
