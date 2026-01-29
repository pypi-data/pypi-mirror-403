import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import numpy as np

# 1. 選擇底圖來源（Google 衛星影像）
# 註：某些來源可能需要 API Key 或因網路環境受限，可換成 StamenTerrain
import cartopy.io.img_tiles as cimgt
request = cimgt.GoogleTiles(style='satellite')
ax = plt.axes(projection=request.crs)

fig = plt.figure(figsize=(10, 8))


# 2. 設定顯示範圍 [min_lon, max_lon, min_lat, max_lat]
extent = [120.5, 121.5, 23.5, 24.5] # 以台灣中部為例
ax.set_extent(extent)

# 3. 添加衛星底圖 (zoom 等級視範圍調整，通常 8-12 較合適)
ax.add_image(request, 10)

# --- 模擬土地利用變遷數據 ---
lon = np.linspace(120.5, 121.5, 100)
lat = np.linspace(23.5, 24.5, 100)
lon2d, lat2d = np.meshgrid(lon, lat)
# 假設 1=森林, 2=城鎮, 3=水體
data = np.random.randint(1, 4, size=(100, 100)) 
# --------------------------

# 4. 繪製 pcolormesh
# transform=ccrs.PlateCarree() 確保經緯度數據正確轉換到底圖投影
# alpha=0.5 讓下方的衛星圖透出來
#mesh = ax.pcolormesh(lon2d, lat2d, data, 
#                    transform=ccrs.PlateCarree(), 
#                    cmap='viridis', 
#                    alpha=0.4, 
#                    shading='auto')

# 添加格線與標籤
gl = ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
gl.top_labels = False
gl.right_labels = False

plt.title("Land Use Change Overlay on Satellite Imagery", pad=20)
plt.show()