import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

app=Flask(__name__)
app.secret_key=os.environ.get("FLASK_SECRET_KEY","troque-esta-chave-no-render")
supabase=create_client(os.environ["SUPABASE_URL"],os.environ["SUPABASE_KEY"])
ADMIN_USER=os.environ.get("ADMIN_USER","admin")
ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD","admin123")

def admin_required(f):
    @wraps(f)
    def w(*a,**k):
        if not session.get("admin_logado"): return redirect(url_for("login"))
        return f(*a,**k)
    return w

def v(n): return request.form.get(n,"").strip()

@app.route("/")
def index(): return render_template("index.html")

@app.route("/cadastro",methods=["GET","POST"])
def cadastro():
    if request.method=="POST":
        d={x:v(x) for x in ["nome","email","telefone","cpf","data_nascimento","cep","endereco","numero","complemento","bairro","cidade","estado","observacoes"]}
        d["data_nascimento"]=d["data_nascimento"] or None
        d["aceite_termos"]=request.form.get("aceite_termos")=="on"
        if not d["nome"] or not d["email"] or not d["telefone"] or not d["aceite_termos"]:
            flash("Preencha os campos obrigatórios e aceite os termos.","erro")
            return render_template("cadastro.html",dados=d)
        try:
            supabase.table("clientes").insert(d).execute()
            flash("Cadastro realizado com sucesso!","sucesso")
            return redirect(url_for("cadastro"))
        except Exception as e:
            flash(f"Erro no cadastro: {e}","erro")
            return render_template("cadastro.html",dados=d)
    return render_template("cadastro.html",dados={})

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        if v("usuario")==ADMIN_USER and request.form.get("senha","")==ADMIN_PASSWORD:
            session.clear(); session["admin_logado"]=True
            return redirect(url_for("admin"))
        return render_template("login.html",erro="Usuário ou senha incorretos.")
    return render_template("login.html",erro=None)

@app.route("/logout")
def logout(): session.clear(); return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin():
    try:
        clientes=supabase.table("clientes").select("*").order("id",desc=True).execute().data or []
    except Exception as e:
        clientes=[]; flash(f"Erro ao consultar clientes: {e}","erro")
    return render_template("admin.html",clientes=clientes)

@app.route("/admin/cliente/<int:cid>/editar",methods=["GET","POST"])
@admin_required
def editar(cid):
    r=supabase.table("clientes").select("*").eq("id",cid).limit(1).execute()
    if not r.data: return redirect(url_for("admin"))
    c=r.data[0]
    if request.method=="POST":
        d={x:v(x) for x in ["nome","email","telefone","cpf","data_nascimento","cep","endereco","numero","complemento","bairro","cidade","estado","observacoes"]}
        d["data_nascimento"]=d["data_nascimento"] or None
        try:
            supabase.table("clientes").update(d).eq("id",cid).execute()
            flash("Cadastro atualizado.","sucesso"); return redirect(url_for("admin"))
        except Exception as e: flash(f"Erro: {e}","erro")
    return render_template("editar.html",cliente=c)

@app.route("/admin/cliente/<int:cid>/excluir",methods=["POST"])
@admin_required
def excluir(cid):
    try: supabase.table("clientes").delete().eq("id",cid).execute(); flash("Cadastro excluído.","sucesso")
    except Exception as e: flash(f"Erro: {e}","erro")
    return redirect(url_for("admin"))

@app.route("/admin/senha")
@admin_required
def senha():
    return render_template("senha.html")

@app.route("/health")
def health():
    try: supabase.table("clientes").select("id").limit(1).execute()
    except Exception as e: return {"status":"erro","supabase":str(e)},500
    return {"status":"online","supabase":"conectado"}

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
