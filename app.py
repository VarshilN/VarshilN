from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify
from datetime import datetime, timedelta, date
from jugaad_data.nse import stock_df
from jugaad_data.nse import index_df,history
import plotly.express as px
from jugaad_data.nse import NSELive
import yfinance as yf
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message 
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.secret_key = 'sdsad'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 's29207488@gmail.com'
app.config['MAIL_PASSWORD'] = 'hellobgmi'
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    verified = db.Column(db.Boolean, default=False)
with app.app_context():
    db.create_all()
mail = Mail(app)
selected_stocks=[]
# app=Flask(__name__)
@app.route('/')
def home():
    return render_template('HomePage.html',image_path='images/stock@india.jpeg')
@app.route('/login',methods=['POST'])
def login():
    if request.form.get('method')=='POST':
        name = request.form.get('name')
        password = request.form.get('password')
        user = User.query.filter_by(name=name).first()
        if user and bcrypt.check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            return render_template('dashboard.html')
        else:
            flash('Invalid name or password. Please try again.', 'danger')
            return render_template('login.html')
    else:
        flash('invalid method')
        return redirect(url_for('login'))
email_verification_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])   
@app.route('/register')
def register():
    def send_verification_email(user):
        token = generate_verification_token(user.email)
        subject = 'Account Verification - Your App'
        message = f'Thank you for registering with Your App. Please click the following link to verify your email:\n\n{url_for("verify_email", token=token, _external=True)}'
        send_email(user.email, subject, message)
    def generate_verification_token(email):
    # You can use a more secure method for generating the token
        return email_verification_serializer.dumps(email) 
    def send_email(to, subject, body):
        msg = Message(subject, recipients=[to], body=body)
        mail.send(msg)
    error_message = None  # Initialize error message
    registration_success_message = None  # Initialize success message
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            send_verification_email(new_user)
            registration_success_message = 'Registration successful! A verification email has been sent to your email address. Please check your inbox and click the verification link to activate your account.'
            flash(registration_success_message, 'success')
            return redirect(url_for('registration_success'))
        except IntegrityError:  # Handle unique constraint violation (email already in use)
            db.session.rollback()
            error_message = 'Email is already in use. Please choose a different email.'
    # Render the template with the error message and success message if present
    return render_template('register.html', error_message=error_message, registration_success_message=registration_success_message)  
    # return render_template('register.html')
@app.route('/verify_email/${token}')
def verify_email(token):
    try:
        email = email_verification_serializer.loads(token, max_age=3600)  # Token expires in 1 hour
        user = User.query.filter_by(email=email).first()
        if user:
            user.verified = True
            db.session.commit()
            flash('Email verification successful. You can now log in.', 'success')
        else:
            flash('Invalid verification token. Please try again.', 'danger')
    except SignatureExpired:
        flash('Verification link has expired. Please register again.', 'danger')
    except BadTimeSignature:
        flash('Invalid verification token. Please try again.', 'danger')
    return redirect(url_for('login'))


@app.route('/dashboard',methods=['GET','POST'])
def dashboard():
    return render_template('User.html')
@app.route('/host')
def host():
    gainers=[]
    loosers=[]
    n=NSELive()
    q=n.live_index('NIFTY 50')
    n=NSELive()
    stocks=sorted(q['data'][1:],key=lambda x:x['pChange'],reverse=True)
    gainers=stocks[:11]
    losers=stocks[len(stocks)-12:]
    return render_template('host.html',gainers=gainers,losers=losers)
@app.route('/search')
def search():
    return render_template('searchPanel.html')
@app.route('/plot',methods=['POST','GET'])
def plot():
    def get_stock_info(ticker_symbol):
        stock=yf.Ticker(ticker_symbol)
        market_cap = stock.info.get('marketCap', 'N/A')
        trailing_pe_ratio = stock.info.get('trailingPE', 'N/A')
        pb_ratio = stock.info.get('priceToBook', 'N/A')
        roe = stock.info.get('returnOnEquity', 'N/A')
        peg_ratio = stock.info.get('pegRatio', 'N/A')
        peg_ratio=0
        roe=0 
        dividend_yield = stock.info['dividendYield']
        average_price = stock.info['regularMarketDayHigh'] + stock.info['regularMarketDayLow'] / 2
        dic={'mcap':market_cap,'pe':trailing_pe_ratio,'pb':pb_ratio,'peg':peg_ratio,'roe':roe,'div':dividend_yield,'avg':average_price}
        return dic 
    search_type=request.args['search_type']
    current_date=datetime.now()   
    interval=request.args.get('interval','1w')
    back_date=current_date
    if interval=='1w':
        back_date=current_date-timedelta(weeks=1)  
    if interval == '1M':
        back_date = current_date - timedelta(weeks=4)
    if interval == '1Yr':
        back_date = current_date - timedelta(weeks=52)
    if interval == '3Yr':
        back_date = current_date - timedelta(weeks=3*52)
    if interval == '5Yr':
        back_date = current_date - timedelta(weeks=5*52)
    elif interval=='all':
        back_date=current_date-timedelta(weeks=30*52)
    src=request.args['src']
    n=NSELive()
    market_status_data = n.market_status()
    # market_cap_in_crs = market_status_data.get('marketcap', {}).get('marketCapinCRRupees', None)
    status=market_status_data['marketState'][0]['marketStatus']
    if(search_type=='symbol'):
        df=stock_df(src,from_date=date(back_date.year,back_date.month,back_date.day),to_date=date(current_date.year,current_date.month,current_date.day),series='EQ') 
        symbol=src+'.NS'
        dic=get_stock_info(symbol)
        market_cap=dic['mcap']
        div=dic['div']
        pe=dic['pe']
        pb=dic['pb']
        peg=dic['peg']
        roe=dic['roe']
        avg=dic['avg']
        n=NSELive()
        q=n.stock_quote(src)
        industry=q['info'].get('industry','##')
        dat =df.iloc[0]['DATE']
        dat=date(dat.year,dat.month,dat.day)
        vol = round(df.iloc[0]['VOLUME'],2)
        val =round(df.iloc[0]['VALUE'],2)
        YH = df.iloc[0]['52W H']
        YL = df.iloc[0]['52W L']
        no_of_trades=df.iloc[0]['NO OF TRADES']
        fig = px.line(df, x='DATE', y='HIGH', title=f"{q['info']['companyName']} Stock Price")
        fig_html = fig.to_html()
        return render_template("plot.html",lcp=q['priceInfo']['lowerCP'],ucp=q['priceInfo']['upperCP'],industry=industry,name=q['info']['companyName'],price=q['priceInfo']['lastPrice'],open=q['priceInfo']['open'],close=q['priceInfo']['close'],HIGH=q['priceInfo']['intraDayHighLow']['max'],LOW=q['priceInfo']['intraDayHighLow']['min'],WH=q['priceInfo']['weekHighLow']['max'],WL=q['priceInfo']['weekHighLow']['min'],fig_html=fig_html,src=src,search_type='symbol',isTop10=q['info']['isTop10'],st=status,change=round(q['priceInfo']['change'],2),chg=round(q['priceInfo']['pChange'],2),val=val,vol=vol,YH=YH,YL=YL,dat=dat,notrades=no_of_trades,mcap=market_cap,div=div,pe=pe,pb=pb,roe=roe,avg=avg,peg=peg)
    else:       
# Call index_df function to get historical data
        div='N/A'
        pe='N/A'
        pb='N/A'
        peg='N/A'
        roe='N/A'
        avg='N/A'
        df = history.index_df(symbol=src,from_date=date(back_date.year,back_date.month,back_date.day),to_date=date(current_date.year,current_date.month,current_date.day))
        q=n.live_index(src)
        fig=px.line(df,x='HistoricalDate',y='HIGH',title=f"{q['name']} Stock Price")
        fig_html=fig.to_html()
        vol =q['data'][0]['totalTradedVolume']
        val=q['data'][0]['totalTradedValue']
        dat=date(current_date.year,current_date.month,current_date.day)
        return render_template("plot.html",name=src,price=q['data'][0]['lastPrice'],YH=q['data'][0]['yearHigh'],YL=q['data'][0]['yearLow'],HIGH=q['data'][0]['dayHigh'],LOW=q['data'][0]['dayLow'],open=q['data'][0]['open'],close=q['data'][0]['previousClose'],change=q['data'][0]['change'],chg=q['data'][0]['pChange'],st=status,fig_html=fig_html,src=src,search_type='index',vol=vol,div=div,pe=pe,peg=peg,avg=avg,pb=pb,roe=roe,val=val,dat=dat) 
@app.route('/user')
def user():
    return render_template('compare_stocks.html')
@app.route('/compare_stocks')

def compare_stocks():
    if 'remove_graph' in request.args:
        selected_stocks.clear()
        graph_html=None
        return render_template('compare_stocks.html')
    else:
        symbol=str(request.args.get('src'))
        interval=str(request.args.get('interval','1w'))
        selected_stocks.append(symbol)
        current_date=datetime.now()   
        back_date=current_date-timedelta(weeks=1)  
        if interval == '1M':
            back_date = current_date - timedelta(weeks=4)    
        elif interval == '1Yr':
            back_date = current_date - timedelta(weeks=52)
        elif interval == '3Yr':
            back_date = current_date - timedelta(weeks=3*52)
        elif interval == '5Yr':
            back_date = current_date - timedelta(weeks=5*52)
        elif interval=='All':
            back_date=date(0,0,0)
        fig=px.line()
        for symbol in selected_stocks:
            df=stock_df(symbol=symbol,from_date=date(back_date.year,back_date.month,back_date.day),to_date=date(current_date.year,current_date.month,current_date.day),series='EQ')
            fig.add_scatter(x=df['DATE'],y=df['HIGH'],mode='lines',name=f'{symbol}Close Price')
            fig.update_layout(title='Stock Price Comparison', xaxis_title='Date', yaxis_title='Close Price')
        graph_html = fig.to_html(full_html=False)
        return render_template('compare_stocks.html',selected_stocks=selected_stocks,graph_html=graph_html)
@app.route('/get_filters')                                                                                                 
def get_filters():
    return render_template('filters.html')
@app.route('/filters')
def filters():
    src=request.args.get('src')
    def get_stock_info(ticker_symbol):
        stock=yf.Ticker(ticker_symbol)
        market_cap = stock.info.get('marketCap', 'N/A')
        trailing_pe_ratio = stock.info.get('trailingPE', 'N/A')
        pb_ratio = stock.info.get('priceToBook', 'N/A')
        roe = stock.info.get('returnOnEquity', 'N/A')
        peg_ratio = stock.info.get('pegRatio', 'N/A')
        peg_ratio=0
        roe=0 
        dividend_yield = stock.info['dividendYield']
        average_price = stock.info['regularMarketDayHigh'] + stock.info['regularMarketDayLow'] / 2
        dic={'mcap':market_cap,'pe':trailing_pe_ratio,'pb':pb_ratio,'peg':peg_ratio,'roe':roe,'div':dividend_yield,'avg':average_price}
        return dic  
    n=NSELive()
    def get_stocks_from_index(index_symbol):
        q=n.live_index(index_symbol)
        cnt=0
        for stk in q['data']:
            if cnt==0:
                cnt=1
                continue
            sym=stk['symbol']+'.NS'
            dic=get_stock_info(sym)
            dic['sym']=stk['symbol']
            dic['pchg']=stk['pChange']
            dic['cname']=stk['meta']['companyName']
            filtered_stocks.append(dic)
    def custom_sort(item):
        # Function to use for custom sorting
        # If the value is 'N/A', return a large value to push it to the end
        return item[selected] if item[selected] != 'N/A' else -float('inf')
    filtered_stocks=[]
    get_stocks_from_index(src)
    idx=src
    selected=request.args.get('filters')
    if selected=='pchg':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,idx=idx,flag=1)
    elif selected=='peg':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,flag=5)
    elif selected=='pe':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,flag=3)
    elif selected=='avg':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,idx=idx,flag=2)
    elif selected=='pb':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,flag=4)
    elif selected=='mcap':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,flag=8)
    elif selected=='roe':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,flag=6)
    elif selected=='div':
        filtered_stocks=sorted(filtered_stocks,key=custom_sort,reverse=True)
        return render_template('filters.html',filtered_stocks=filtered_stocks,idx=idx,flag=7)
@app.route('/watchList')
def watchList():
    return render_template('watchlist.html')
@app.route('/add_stock')
def add_stock():
    selected=request.args.get('search_type')
    src=request.args.get('src')
    n=NSELive()
    if selected=='symbol':
        market_status_data = n.market_status()
        market_cap_in_crs = market_status_data.get('marketcap', {}).get('marketCapinCRRupees', None)
        status=market_status_data['marketState'][0]['marketStatus']
        q=n.stock_quote(src)['priceInfo']
        return jsonify({
            'sym': src,
            'lp': round(q['lastPrice'],2),
            'change': round(q['change'],2),
            'chg':round(q['pChange'],2),
            'st': status,
            'vwp': round(q['vwap'],2),
            'cp': round(market_cap_in_crs,3)
        })
if __name__ == '__main__':
    app.run(debug=True)