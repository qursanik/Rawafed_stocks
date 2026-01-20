import streamlit as st
import pandas as pd
import altair as alt

# --- إعداد الصفحة ---
st.set_page_config(page_title="بورصة روافد", layout="wide", page_icon="📈")

# --- تنسيق الواجهة ---
st.markdown("""
<style>
    .metric-card {background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; text-align: center;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# التغيير هنا: قراءة البيانات من ملف الإكسل
# ---------------------------------------------------------
try:
    # قراءة الملف (تأكد أن الملف بجانب كود البايثون مباشرة)
    # engine='openpyxl' ضروري لملفات xlsx
    df = pd.read_excel('market_data.xlsx', engine='openpyxl')
    
    # التأكد من أن العمود الأول هو نص (عشان أسماء الأسابيع)
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    
except FileNotFoundError:
    st.error("⚠️ ملف البيانات غير موجود! تأكد من وجود ملف باسم 'market_data.xlsx' بجانب الكود.")
    st.stop()
except Exception as e:
    st.error(f"حدث خطأ في قراءة الملف: {e}")
    st.stop()

# تحديد اسم عمود الأسابيع (نفترض أنه العمود الأول)
week_column = df.columns[0]
week_order = df[week_column].tolist() # لحفظ ترتيب الأسابيع كما في الملف

# تحويل البيانات لشكل مناسب للرسم (Long Format)
# id_vars هو العمود الثابت (الأسبوع)، وباقي الأعمدة هي الشركات
df_melted = df.melt(id_vars=[week_column], var_name='الشركة (المجموعة)', value_name='سعر السهم')

# --- القائمة الجانبية: محاكي التداول ---
st.sidebar.header("💰 محفظة المستثمر")

if 'balance' not in st.session_state:
    st.session_state.balance = 1000 
if 'portfolio' not in st.session_state:
    # نأخذ أسماء الشركات من أعمدة ملف الإكسل (باستثناء عمود الأسبوع)
    group_names = [col for col in df.columns if col != week_column]
    st.session_state.portfolio = {group: 0 for group in group_names}

st.sidebar.metric("الرصيد المتاح", f"{st.session_state.balance:.2f} ريال")
st.sidebar.markdown("---")

# اختيار الشركة (من الأعمدة الموجودة في الملف)
group_list = [col for col in df.columns if col != week_column]
selected_group = st.sidebar.selectbox("اختر الشركة", group_list)

# جلب آخر سعر متاح في الملف
current_price = df[selected_group].iloc[-1]
st.sidebar.info(f"سعر سهم {selected_group}: **{current_price:.2f}**")

buy_amount = st.sidebar.number_input("الكمية", min_value=1, value=1)
if st.sidebar.button("شراء ✅"):
    cost = buy_amount * current_price
    if st.session_state.balance >= cost:
        st.session_state.balance -= cost
        st.session_state.portfolio[selected_group] += buy_amount
        st.sidebar.success(f"تم الشراء!")
        st.rerun() # تحديث الصفحة
    else:
        st.sidebar.error("رصيدك غير كافي!")

st.sidebar.markdown("---")
st.sidebar.subheader("ممتلكاتك:")
for grp, qty in st.session_state.portfolio.items():
    if qty > 0:
        st.sidebar.write(f"🔹 {grp}: {qty} سهم")

# --- الواجهة الرئيسية ---
st.title("📈 مؤشر سوق روافد (Live)")

# زر تحديث البيانات (مفيد إذا عدلت الإكسل والبرنامج مفتوح)
if st.button('تحديث البيانات من الإكسل 🔄'):
    st.rerun()

# 1. أبرز المؤشرات
st.subheader("📊 ملخص السوق")
cols = st.columns(3)
latest_prices = df.iloc[-1, 1:].sort_values(ascending=False)

for i, (group_name, price) in enumerate(latest_prices.items()):
    col_idx = i % 3
    # حساب التغير (نتأكد أن هناك أكثر من أسبوع واحد للمقارنة)
    if len(df) > 1:
        prev_price = df.iloc[-2][group_name]
        delta = price - prev_price
    else:
        delta = 0
    cols[col_idx].metric(label=group_name, value=f"{price:.2f}", delta=f"{delta:.2f}")

# 2. الرسم البياني
st.markdown("---")
st.subheader("تحليل المسار")

chart = alt.Chart(df_melted).mark_line(point=True).encode(
    x=alt.X(week_column, sort=week_order, title='الأسابيع'),
    y=alt.Y('سعر السهم', title='معدل النقاط'),
    color=alt.Color('الشركة (المجموعة)', title='المجموعة'),
    tooltip=[week_column, 'الشركة (المجموعة)', 'سعر السهم']
).properties(height=400).interactive()

st.altair_chart(chart, use_container_width=True)
