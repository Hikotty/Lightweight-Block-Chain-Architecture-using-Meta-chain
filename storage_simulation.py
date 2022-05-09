import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

DIR = './'

#パラメータ設定
B_block = 100000
B_meta = 150
p_attack = 0.01
max_N_block = 10001
N_node = 100000

#変数の準備
result = []
result2 = []
file_name = DIR + "storage_simulation" + ".png"

#ストレージ容量の計算
for k in range(1,10):
    k = int((k/10)*N_node)
    tmp = []
    for N_block in range(1,max_N_block):
        improved_BC = ((k/N_node)*B_block*N_block + B_meta*N_block)/(10**6)
        tmp.append(improved_BC)
    result2.append(tmp[-1])
    result.append(tmp)
nomal_BC_storage = [B_block*N_block/(10**6) for N_block in range(1,max_N_block)]

#横軸の設定
N_block_list = [int(i) for i in range(1,max_N_block)]

#グラフの描画
plt.figure(figsize=(10,8))
plt.gca().get_yaxis().set_major_locator(ticker.MaxNLocator(integer=True))
cm = plt.get_cmap("Reds")
colors = [cm(0.1), cm(0.2), cm(0.3), cm(0.4), cm(0.5),cm(0.6), cm(0.7), cm(0.8), cm(0.9), cm(1.0)]
plt.xlabel('Cumulative number of blocks')
plt.ylabel('Strage (MB)')
i = 1
con_BC_label="Conventional BC(k="+str(N_node)+")"
plt.plot(N_block_list,nomal_BC_storage,label=con_BC_label)
for res in result:
    label_k = int((i/10)*N_node)
    label_ = "k=" + str(label_k)
    plt.plot(N_block_list,res,label=label_,color=colors[-i])
    i += 1
plt.grid()
plt.legend()
plt.savefig(file_name)

#シミュレーション結果の出力
print("Strage Required when 10000th block made.\n")
print("Conventional BC:",nomal_BC_storage[-1],"MB")
for res in result2:
    print("k =",(result2.index(res)+1)*10000,":storage:",res,"MB ",round(100-(res/nomal_BC_storage[-1])*100,2),"% reduced.")
