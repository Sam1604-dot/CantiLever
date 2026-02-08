# scraper_app.py
# Web Scraper Streamlit Application
# Run with: streamlit run scraper_app.py

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import base64
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Web Scraper Tool",
    page_icon="🛍️",
    layout="wide"
)

# Set visualization style
sns.set_style("whitegrid")

# Title
st.title("🛍️ E-commerce Web Scraper")
st.markdown("*Scrape, analyze, and visualize product data from e-commerce websites*")

# Sidebar
st.sidebar.header("⚙️ Settings")
max_products = st.sidebar.slider("Max products to scrape", 10, 100, 50)
show_stats = st.sidebar.checkbox("Show statistics", value=True)
show_charts = st.sidebar.checkbox("Show visualizations", value=True)

# Info box about supported sites
with st.sidebar.expander("ℹ️ Supported Websites"):
    st.markdown("""
    **Test websites (safe for scraping):**
    - https://books.toscrape.com/
    - https://quotes.toscrape.com/
    - https://scrapethissite.com/
    
    **Note:** Always respect robots.txt and terms of service!
    """)

# Main scraping function
@st.cache_data(ttl=3600)  # Cache for 1 hour
def scrape_website(url, max_items=50):
    """Scrape products from website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        products = []
        
        # Strategy for books.toscrape.com
        if 'books.toscrape.com' in url:
            books = soup.find_all('article', class_='product_pod')[:max_items]
            
            for book in books:
                try:
                    title = book.find('h3').find('a').get('title', 'N/A')
                    price_text = book.find('p', class_='price_color').text.strip()
                    price = float(price_text.replace('£', '').replace('$', ''))
                    
                    rating_element = book.find('p', class_='star-rating')
                    rating_class = rating_element.get('class', [])
                    rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
                    rating = rating_map.get(rating_class[1], 0) if len(rating_class) > 1 else 0
                    
                    availability = book.find('p', class_='instock availability')
                    in_stock = 'In stock' in availability.text.strip() if availability else False
                    
                    products.append({
                        'Title': title,
                        'Price': price,
                        'Rating': rating,
                        'In_Stock': in_stock,
                        'Category': 'Books'
                    })
                except Exception as e:
                    continue
        
        # Strategy for quotes.toscrape.com
        elif 'quotes.toscrape.com' in url:
            quotes = soup.find_all('div', class_='quote')[:max_items]
            
            for quote in quotes:
                try:
                    text = quote.find('span', class_='text').text.strip()
                    author = quote.find('small', class_='author').text.strip()
                    
                    products.append({
                        'Title': f'Quote by {author}',
                        'Price': 0.0,
                        'Rating': 5.0,
                        'In_Stock': True,
                        'Category': 'Quotes'
                    })
                except Exception as e:
                    continue
        
        else:
            st.warning("⚠️ This website might not be supported. Try books.toscrape.com or quotes.toscrape.com")
            return pd.DataFrame()
        
        return pd.DataFrame(products)
    
    except requests.RequestException as e:
        st.error(f"❌ Error fetching website: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Scraping error: {str(e)}")
        return pd.DataFrame()

# Function to create download link for CSV
def get_csv_download_link(df, filename="data.csv"):
    """Generate a download link for CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">📥 Download CSV</a>'
    return href

# Function to create download link for Excel
def get_excel_download(df, filename="data.xlsx"):
    """Generate Excel file for download"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        
        # Add summary sheet
        if not df.empty:
            summary = df.groupby('Rating').agg({
                'Price': ['mean', 'min', 'max', 'count']
            }).round(2)
            summary.to_excel(writer, sheet_name='Summary')
    
    return output.getvalue()

# Main app
st.markdown("---")

# Input section
col1, col2 = st.columns([3, 1])

with col1:
    url = st.text_input(
        "🌐 Website URL", 
        value="https://books.toscrape.com/",
        help="Enter the URL of the e-commerce website to scrape",
        placeholder="https://example.com"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    scrape_button = st.button("🚀 Start Scraping", type="primary", use_container_width=True)

# Scraping logic
if scrape_button:
    if url:
        with st.spinner("🔄 Scraping data... This may take a few seconds..."):
            df = scrape_website(url, max_products)
            
            if not df.empty:
                st.success(f"✅ Successfully scraped {len(df)} products!")
                
                # Store in session state
                st.session_state['df'] = df
                st.session_state['url'] = url
                st.session_state['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                st.warning("⚠️ No products found. Try a different URL or check if the website is accessible.")
    else:
        st.error("❌ Please enter a URL")

# Display results if data exists
if 'df' in st.session_state and not st.session_state['df'].empty:
    df = st.session_state['df']
    
    st.markdown("---")
    st.header("📊 Results")
    
    # Stats
    if show_stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Products", len(df))
        
        with col2:
            avg_price = df['Price'].mean()
            st.metric("Avg Price", f"${avg_price:.2f}")
        
        with col3:
            avg_rating = df['Rating'].mean()
            st.metric("Avg Rating", f"{avg_rating:.2f} ⭐")
        
        with col4:
            in_stock_pct = (df['In_Stock'].sum() / len(df) * 100)
            st.metric("In Stock", f"{in_stock_pct:.1f}%")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Data Table", "📈 Visualizations", "📥 Export", "📊 Analytics"])
    
    with tab1:
        st.subheader("Product Data")
        
        # Search box
        search = st.text_input("🔍 Search products", "", key="search_box")
        
        # Filter data
        if search:
            mask = df['Title'].str.contains(search, case=False, na=False)
            filtered_df = df[mask]
            st.info(f"Found {len(filtered_df)} products matching '{search}'")
            st.dataframe(filtered_df, use_container_width=True, height=400)
        else:
            st.dataframe(df, use_container_width=True, height=400)
        
        # Summary statistics
        with st.expander("📊 View Summary Statistics"):
            st.write(df.describe())
    
    with tab2:
        if show_charts:
            st.subheader("Data Visualizations")
            
            # Create visualizations
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 1. Price distribution
            axes[0, 0].hist(df['Price'], bins=20, color='skyblue', edgecolor='black')
            axes[0, 0].set_title('Price Distribution', fontweight='bold')
            axes[0, 0].set_xlabel('Price ($)')
            axes[0, 0].set_ylabel('Frequency')
            axes[0, 0].axvline(df['Price'].mean(), color='red', linestyle='--', 
                              label=f'Mean: ${df["Price"].mean():.2f}')
            axes[0, 0].legend()
            
            # 2. Price vs Rating scatter
            axes[0, 1].scatter(df['Rating'], df['Price'], alpha=0.6, s=100, color='coral')
            axes[0, 1].set_title('Price vs Rating', fontweight='bold')
            axes[0, 1].set_xlabel('Rating')
            axes[0, 1].set_ylabel('Price ($)')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. Average price by rating
            if df['Rating'].nunique() > 1:
                rating_price = df.groupby('Rating')['Price'].mean().sort_index()
                axes[1, 0].bar(rating_price.index, rating_price.values, 
                              color='lightgreen', edgecolor='black')
                axes[1, 0].set_title('Average Price by Rating', fontweight='bold')
                axes[1, 0].set_xlabel('Rating')
                axes[1, 0].set_ylabel('Average Price ($)')
                axes[1, 0].set_xticks(rating_price.index)
            
            # 4. Rating distribution
            rating_counts = df['Rating'].value_counts().sort_index()
            colors = sns.color_palette('pastel')[0:len(rating_counts)]
            axes[1, 1].pie(rating_counts.values, labels=rating_counts.index, 
                          autopct='%1.1f%%', colors=colors, startangle=90)
            axes[1, 1].set_title('Rating Distribution', fontweight='bold')
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Additional chart - Price trend
            st.subheader("📈 Price Analysis")
            col1, col2 = st.columns(2)
            
            with col1:
                # Box plot
                fig2, ax2 = plt.subplots(figsize=(8, 6))
                df.boxplot(column='Price', by='Rating', ax=ax2)
                ax2.set_title('Price Distribution by Rating')
                ax2.set_xlabel('Rating')
                ax2.set_ylabel('Price ($)')
                plt.suptitle('')
                st.pyplot(fig2)
            
            with col2:
                # Top 10 most expensive
                st.markdown("**💰 Top 10 Most Expensive Products**")
                top_10 = df.nlargest(10, 'Price')[['Title', 'Price', 'Rating']]
                st.dataframe(top_10, hide_index=True)
        else:
            st.info("Enable 'Show visualizations' in sidebar to view charts")
    
    with tab3:
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV download
            st.markdown("### 📄 CSV Format")
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"scraped_products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Excel download
            st.markdown("### 📊 Excel Format")
            excel_data = get_excel_download(df)
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name=f"product_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        
        with col3:
            # JSON download
            st.markdown("### 📋 JSON Format")
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Report
        st.markdown("---")
        st.markdown("### 📝 Analysis Report")
        
        report = f"""
**Web Scraping Report**

Source: {st.session_state['url']}
Scraped: {st.session_state['scraped_at']}

Dataset Summary:
- Total Products: {len(df)}
- Price Range: ${df['Price'].min():.2f} - ${df['Price'].max():.2f}
- Average Price: ${df['Price'].mean():.2f}
- Median Price: ${df['Price'].median():.2f}
- Average Rating: {df['Rating'].mean():.2f} ⭐
- In Stock: {df['In_Stock'].sum()} ({df['In_Stock'].sum()/len(df)*100:.1f}%)

Top 5 Products by Price:
{df.nlargest(5, 'Price')[['Title', 'Price', 'Rating']].to_string(index=False)}

Rating Distribution:
{df['Rating'].value_counts().sort_index().to_string()}
        """
        
        st.text_area("Report Preview", report, height=300)
        
        st.download_button(
            label="📥 Download Report (TXT)",
            data=report,
            file_name=f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with tab4:
        st.subheader("📊 Advanced Analytics")
        
        # Statistical analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Statistical Summary")
            stats_df = pd.DataFrame({
                'Metric': ['Count', 'Mean', 'Std Dev', 'Min', '25%', 'Median', '75%', 'Max'],
                'Price': [
                    len(df),
                    df['Price'].mean(),
                    df['Price'].std(),
                    df['Price'].min(),
                    df['Price'].quantile(0.25),
                    df['Price'].median(),
                    df['Price'].quantile(0.75),
                    df['Price'].max()
                ],
                'Rating': [
                    len(df),
                    df['Rating'].mean(),
                    df['Rating'].std(),
                    df['Rating'].min(),
                    df['Rating'].quantile(0.25),
                    df['Rating'].median(),
                    df['Rating'].quantile(0.75),
                    df['Rating'].max()
                ]
            })
            st.dataframe(stats_df.set_index('Metric').round(2))
        
        with col2:
            st.markdown("### 💡 Insights")
            
            # Generate insights
            insights = []
            
            # Price insights
            if df['Price'].std() > df['Price'].mean():
                insights.append("⚠️ High price variance - wide range of product prices")
            
            # Rating insights
            avg_rating = df['Rating'].mean()
            if avg_rating >= 4.5:
                insights.append("⭐ Excellent average rating - highly rated products")
            elif avg_rating >= 4.0:
                insights.append("✅ Good average rating - well-received products")
            else:
                insights.append("📊 Mixed ratings - varied product quality")
            
            # Stock insights
            stock_pct = (df['In_Stock'].sum() / len(df)) * 100
            if stock_pct >= 90:
                insights.append("📦 Excellent availability - most items in stock")
            elif stock_pct >= 70:
                insights.append("📦 Good availability - majority in stock")
            else:
                insights.append("⚠️ Limited availability - many items out of stock")
            
            # Price-rating correlation
            correlation = df['Price'].corr(df['Rating'])
            if abs(correlation) > 0.5:
                trend = "positive" if correlation > 0 else "negative"
                insights.append(f"📊 Strong {trend} correlation between price and rating")
            
            for insight in insights:
                st.info(insight)
        
        # Correlation matrix
        st.markdown("### 🔗 Correlation Analysis")
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 1:
            corr = df[numeric_cols].corr()
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, ax=ax)
            ax.set_title('Feature Correlation Matrix')
            st.pyplot(fig)

else:
    # Welcome screen
    st.info("👆 Enter a website URL and click 'Start Scraping' to begin!")
    
    st.markdown("### 🎯 Example URLs to Try:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.code("https://books.toscrape.com/")
        st.caption("📚 Practice book store")
    
    with col2:
        st.code("https://quotes.toscrape.com/")
        st.caption("💬 Quotes collection")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Built with Streamlit & BeautifulSoup | Web Scraper Tool v1.0</p>
    <p><small>Always respect robots.txt and website terms of service</small></p>
</div>
""", unsafe_allow_html=True)

# Sidebar - additional info
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 Features
✅ Real-time web scraping  
✅ Data visualization  
✅ Multiple export formats  
✅ Search functionality  
✅ Statistical analysis  
✅ Advanced analytics

### ⚠️ Disclaimer
This tool is for educational purposes.  
Always check website's robots.txt and  
terms of service before scraping.
""")