from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).parent/'equations'
plt.rcParams.update({'mathtext.fontset':'stix','pdf.fonttype':42,'font.family':'DejaVu Sans'})
eqs={
'ranking':r'R_b=(c_{b1},c_{b2},\ldots,c_{b\ell_b}),\qquad w_b\geq 0',
'corank':r'C_{ij}=\sum_b w_b\,\mathbf{1}\{i,j\in R_b\}',
'adjacency':r'A_{ij}=\sum_b w_b\sum_{k=1}^{\ell_b-1}\mathbf{1}\{c_{bk}=i,\ c_{b,k+1}=j\}',
'similarity':r'F_{ij}=\frac{A_{ij}}{C_{ij}}\ (C_{ij}>0),\qquad S_{ij}=\frac{F_{ij}+F_{ji}}{2}',
'dissimilarity':r'\delta_{ij}=\frac{1}{\sqrt{S_{ij}}}\ (S_{ij}>0),\qquad\delta_{ii}=0',
'distance':r'd_{ij}=|x_i-x_j|',
'loss':r'L(x,f)=\sum_{i<j}\left[|x_i-x_j|-f(\delta_{ij})\right]^2',
'stress1':r'\mathrm{Stress\!\!-\!1}=\sqrt{\frac{\sum_{i,j}(d_{ij}-\widehat d_{ij})^2}{\sum_{i,j}\widehat d_{ij}^{\,2}}}',
'center':r'\widetilde{x}_i^{(r)}=x_i^{(r)}-\frac{1}{m}\sum_{j=1}^{m}x_j^{(r)}',
'mean':r'\bar{x}_i=\frac{1}{|\mathcal{R}^{*}|}\sum_{r\in\mathcal{R}^{*}}\widetilde{x}_i^{(r)}',
'normalize':r'z_i=\frac{\bar{x}_i-\min_j\bar{x}_j}{\max_j\bar{x}_j-\min_j\bar{x}_j},\qquad z_i^{\prime}=1-z_i',
'compatibility':r'\exists\,u\in[0,1]:\quad |u-z_{c_1}|<|u-z_{c_2}|<\cdots<|u-z_{c_\ell}|',
'gamma':r'\gamma_G=\frac{\sum_{b\in G}w_b\,\mathbf{1}\{R_b\ \mathrm{is\ compatible}\}}{\sum_{b\in G}w_b}'
}
for key,expr in eqs.items():
 fig=plt.figure(figsize=(7,1));fig.text(0,.5,'$'+expr+'$',fontsize=16,color='#24384F',va='center')
 fig.savefig(BASE/(key+'.pdf'),bbox_inches='tight',pad_inches=.08,transparent=True)
 plt.close(fig)
print('Vector equation PDFs:',len(eqs))
