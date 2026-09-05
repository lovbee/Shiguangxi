<template>
  <div class="min-h-screen bg-white">
    <!-- 搜索结果分类导航 -->
    <div class="border-b border-gray-100">
      <div class="flex items-center my-2">
        <nav class="grow">
          <ul class="flex items-center">
            <li v-for="category in categories" :key="category.name">
              <a 
              @click="handleTabChange(category.type)"
                href="#" 
                class="px-4 py-2 rounded-full transition-colors h-[40px] hover:bg-[#f4f4f4]"
                :class="selectedType === category.type ? 'bg-[#f4f4f4] text-[#333] font-bold' : 'text-[#666] hover:text-[#333]'"
              >
                {{ category.name }}
              </a>
            </li>
          </ul>
        </nav>
        <div
        class="cursor-pointer flex items-center px-3 hover:bg-[#f4f4f4] rounded-full text-[#666] hover:text-[#333] relative h-[40px]">
          <div v-if="selectedType !== 2" class="flex items-center" @click="showFilter = !showFilter">
            <svg t="1740221132886" class="icon w-5 h-5" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="16352" width="200" height="200"><path d="M387.1 864.3c-9.9 0-19.7-2.5-28.6-7.6-18-10.3-29.1-29.6-29-50.4l1.7-228.9c0-3.5-1-6.9-2.9-9.9L133.5 268.2c-16.6-25.6-17.9-58.1-3.2-84.8 14.5-26.6 42.3-43 72.6-43h0.6l491.8 3.6c30.5 0.2 58.3 17.1 72.5 44.1 14.3 27 12.5 59.4-4.5 84.8L564.1 569.2c-2 2.9-3 6.3-3 9.8l-1.2 159c-0.1 20-10.9 38.7-28 49l-115.3 69.1c-9 5.4-19.3 8.2-29.5 8.2zM202.8 205.2c-9.5 0-14.1 6.5-15.7 9.3-1.6 2.8-4.6 10.3 0.7 18.3l194.8 299.3c8.9 13.6 13.5 29.4 13.4 45.7l-1.6 216 100.7-60.4 1.1-154.9c0.1-16.3 5-32 14.1-45.5l199.1-296.4c5.4-8 2.5-15.5 1-18.3-1.5-2.8-6-9.5-15.7-9.5l-491.8-3.6h-0.1z" fill="#707070" p-id="16353"></path><path d="M825.2 599.6h-169c-17.9 0-32.4-14.5-32.4-32.4s14.5-32.4 32.4-32.4h169c17.9 0 32.4 14.5 32.4 32.4s-14.5 32.4-32.4 32.4zM825.2 717.5h-169c-17.9 0-32.4-14.5-32.4-32.4s14.5-32.4 32.4-32.4h169c17.9 0 32.4 14.5 32.4 32.4s-14.5 32.4-32.4 32.4zM825.2 835.5h-169c-17.9 0-32.4-14.5-32.4-32.4s14.5-32.4 32.4-32.4h169c17.9 0 32.4 14.5 32.4 32.4s-14.5 32.4-32.4 32.4z" fill="#707070" p-id="16354"></path></svg>
            <div>筛选</div>
          </div>

          <!-- 筛选弹出框 -->
          <div 
            v-if="showFilter" 
            ref="filterRef"
            class="absolute right-0 top-12 w-[460px] bg-white rounded-lg shadow-lg p-5 z-50 border border-gray-100"
          >
            <div class="space-y-5">
              <!-- 排序依据 -->
              <div>
                <div class="text-gray-600 font-medium mb-3 text-xs">排序依据</div>
                <div class="grid grid-cols-3 gap-2">
                  <button 
                    v-for="sort in sortOptions" 
                    :key="sort.value"
                    class="px-3 py-2 rounded-full text-sm inline-flex items-center justify-center"
                    :class="selectedSort === sort.value ? 'border border-[#ff2442] text-[#ff2442] bg-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                    @click="selectedSort = sort.value"
                  >
                    <div class="flex items-center justify-center">
                      <span>{{ sort.label }}</span>
                      <svg 
                        v-if="selectedSort === sort.value"
                        class="w-3 h-3 ml-1" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor"
                      >
                        <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </button>
                </div>
              </div>

              <!-- 笔记类型 -->
              <div>
                <div class="text-gray-600 font-medium mb-3 text-xs">笔记类型</div>
                <div class="grid grid-cols-3 gap-2">
                  <button 
                    v-for="type in noteTypes" 
                    :key="type.value"
                    class="px-3 py-2 rounded-full text-sm inline-flex items-center justify-center"
                    :class="selectedType === type.value ? 'border border-[#ff2442] text-[#ff2442] bg-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                    @click="selectedType = type.value"
                  >
                    <div class="flex items-center justify-center">
                      <span>{{ type.label }}</span>
                      <svg 
                        v-if="selectedType === type.value"
                        class="w-3 h-3 ml-1" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor"
                      >
                        <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </button>
                </div>
              </div>

              <!-- 发布时间 -->
              <div>
                <div class="text-gray-600 font-medium mb-3 text-xs">发布时间</div>
                <div class="grid grid-cols-3 gap-2">
                  <button 
                    v-for="time in timeFilters" 
                    :key="time.value"
                    class="px-3 py-2 rounded-full text-sm inline-flex items-center justify-center"
                    :class="selectedTime === time.value ? 'border border-[#ff2442] text-[#ff2442] bg-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                    @click="selectedTime = time.value"
                  >
                    <div class="flex items-center justify-center">
                      <span>{{ time.label }}</span>
                      <svg 
                        v-if="selectedTime === time.value"
                        class="w-3 h-3 ml-1" 
                        viewBox="0 0 24 24" 
                        fill="none" 
                        stroke="currentColor"
                      >
                        <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </div>
                  </button>
                </div>
              </div>

              <!-- 底部按钮 -->
              <div class="flex gap-2 pt-2">
                <button 
                  class="cursor-pointer flex-1 h-10 font-bold rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50"
                  @click="resetFilters"
                >
                  重置
                </button>
                <button 
                  class="cursor-pointer flex-1 h-10 font-bold rounded-full bg-[#ff2442] text-white hover:opacity-90"
                  @click="applyFilters"
                >
                  确定
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- 搜索结果内容 -->
    <div class="container mx-auto mt-6">

      <LoadingSpinner ref="loadingRef"/>  

      <!-- 瀑布流布局 -->
      <div v-if="activeTab !== 'users'" class="masonry-container">
        <div v-for="note in searchResults" :key="note.id" class="masonry-item">
          <NoteCard :note="note" @click="onNoteClick" />
        </div>
      </div>

      <!-- 用户列表 -->
      <div v-else>
        <div v-for="user in searchResults" :key="user.id" class="flex flex-col">
          <UserCard 
            :user="user" 
            @follow="handleFollowUser"
            @login-required="handleLoginRequired"
          />
            </div>
          </div>

      <div v-if="!searchResults || searchResults.length == 0" class="flex flex-col justify-center items-center">
        <div>
          <svg class="icon w-[26rem] mt-10" height="250" node-id="1" sillyvg="true" template-height="250" template-width="400" version="1.1" viewBox="0 0 400 250" width="400" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><defs node-id="72"><linearGradient gradientUnits="objectBoundingBox" id="linearGradient1" node-id="74" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f8f8f8" stop-opacity="0.082"/><stop offset="1" stop-color="#7c7c7c" stop-opacity="0.059"/></linearGradient><linearGradient gradientUnits="objectBoundingBox" id="linear-gradient-2" node-id="6" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f0eeef" stop-opacity="0"/><stop offset="1" stop-color="#d5d5d5"/></linearGradient><linearGradient gradientUnits="objectBoundingBox" id="linear-gradient" node-id="3" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f8f8f8" stop-opacity="0.082"/><stop offset="1" stop-color="#7c7c7c" stop-opacity="0.059"/></linearGradient></defs><g node-id="289"><path d="M 0.00 0.00 L 400.00 0.00 L 400.00 250.00 L 0.00 250.00 Z" fill="none" group-id="1" id="矩形_2862" node-id="10" stroke="none" target-height="250" target-width="400" target-x="0" target-y="0"/></g><g node-id="290"><g node-id="291"><g node-id="328"><path d="M 194.40 91.00 L 206.40 91.00 L 217.50 91.50 L 227.90 92.50 L 237.40 94.00 L 247.10 96.00 L 256.10 98.40 L 264.30 101.00 L 272.00 104.00 L 279.60 107.50 L 286.60 111.20 L 293.10 115.10 L 299.00 119.10 L 310.20 128.10 L 319.40 137.40 L 325.00 144.00 L 329.80 150.50 L 333.90 156.90 L 340.90 169.80 L 343.60 175.60 L 346.90 184.40 L 349.10 191.70 L 350.70 198.50 L 351.40 203.10 L 351.60 207.00 L 351.40 208.00 L 48.40 208.00 L 49.20 199.90 L 52.00 186.80 L 56.60 172.80 L 62.30 160.40 L 65.80 154.20 L 70.00 147.80 L 74.80 141.30 L 83.10 132.00 L 93.20 122.90 L 98.60 118.80 L 104.70 114.80 L 111.30 110.90 L 118.50 107.20 L 125.70 104.00 L 133.70 101.00 L 142.40 98.30 L 151.80 96.00 L 161.20 94.10 L 171.30 92.60 L 182.40 91.60 L 194.40 91.00 Z" fill="url(#linearGradient1)" fill-rule="nonzero" group-id="2,3,40" id="路径_8418" node-id="13" stroke="none" target-height="117" target-width="303.2" target-x="48.4" target-y="91"/></g><g node-id="329"><path d="M 392.50 207.70 L 392.20 208.80 L 391.20 210.10 L 389.20 211.50 L 385.60 213.10 L 381.00 214.60 L 374.70 216.20 L 366.20 217.90 L 353.00 220.00 L 336.10 222.10 L 318.10 223.70 L 297.20 225.20 L 275.30 226.40 L 226.40 227.80 L 200.00 228.00 L 173.60 227.80 L 124.70 226.40 L 102.80 225.20 L 81.90 223.70 L 63.90 222.10 L 47.00 220.00 L 33.80 217.90 L 25.30 216.20 L 14.40 213.10 L 10.80 211.50 L 8.80 210.10 L 7.80 208.80 L 7.50 207.70 L 7.80 206.50 L 8.80 205.30 L 10.80 203.90 L 14.40 202.30 L 19.00 200.70 L 33.80 197.40 L 47.00 195.30 L 63.90 193.30 L 81.90 191.60 L 102.80 190.10 L 124.70 188.90 L 173.60 187.50 L 200.00 187.30 L 226.40 187.50 L 275.30 188.90 L 297.20 190.10 L 318.10 191.60 L 336.10 193.30 L 353.00 195.30 L 366.20 197.40 L 374.70 199.10 L 381.00 200.70 L 385.60 202.30 L 389.20 203.90 L 391.20 205.30 L 392.20 206.50 L 392.50 207.70 Z" fill="url(#linear-gradient-2)" fill-opacity="0.6" fill-rule="nonzero" group-id="2,3,41" id="椭圆_622" node-id="14" stroke="none" target-height="40.699997" target-width="385" target-x="7.5" target-y="187.3"/></g><g node-id="330"><g node-id="335"><path d="M 194.40 43.90 L 211.30 44.10 L 226.50 45.80 L 233.50 47.20 L 242.30 49.40 L 250.60 52.10 L 258.40 55.20 L 265.70 58.70 L 272.80 62.60 L 279.50 66.90 L 285.80 71.50 L 291.70 76.40 L 302.50 87.00 L 312.00 98.40 L 317.70 106.40 L 322.80 114.40 L 327.30 122.60 L 335.20 139.10 L 338.30 147.10 L 343.60 162.80 L 348.10 180.30 L 350.90 196.90 L 351.50 202.30 L 351.40 208.00 L 48.40 208.00 L 49.90 191.40 L 53.00 173.50 L 55.40 163.20 L 58.70 151.70 L 61.30 144.00 L 67.90 127.80 L 71.90 119.80 L 76.40 111.80 L 81.40 103.80 L 85.50 98.00 L 94.80 86.90 L 100.00 81.50 L 105.50 76.50 L 111.30 71.70 L 117.70 67.10 L 124.50 62.80 L 131.40 59.00 L 138.90 55.60 L 147.00 52.40 L 155.70 49.70 L 164.30 47.50 L 173.60 45.80 L 183.60 44.60 L 194.40 43.90 Z" fill="url(#linear-gradient)" fill-rule="nonzero" group-id="2,3,42,47" id="路径_8419" node-id="16" stroke="none" target-height="164.1" target-width="303.1" target-x="48.4" target-y="43.9"/></g></g><g node-id="331"><path d="M 150.80 90.00 L 117.40 90.00 L 115.10 89.80 L 112.90 89.10 L 110.90 88.00 L 109.10 86.60 L 107.60 84.80 L 106.50 82.70 L 105.80 80.60 L 105.60 78.20 L 105.90 75.70 L 106.70 73.30 L 108.00 71.10 L 109.20 69.70 L 112.30 67.60 L 114.40 66.80 L 115.80 64.60 L 119.00 61.90 L 122.90 60.40 L 125.10 60.20 L 129.50 61.00 L 131.10 58.50 L 132.50 56.90 L 136.10 54.80 L 138.20 54.20 L 140.30 54.00 L 142.70 54.20 L 144.90 54.90 L 146.90 56.00 L 148.70 57.40 L 150.20 59.20 L 151.30 61.20 L 151.90 63.40 L 152.20 66.50 L 155.70 67.50 L 158.00 68.90 L 159.90 70.70 L 161.30 73.00 L 162.30 75.50 L 162.60 78.20 L 162.40 80.60 L 161.70 82.70 L 160.60 84.80 L 159.10 86.60 L 157.30 88.00 L 155.30 89.10 L 153.10 89.80 L 150.80 90.00 Z" fill="#ececec" fill-rule="nonzero" group-id="2,3,43" node-id="116" stroke="none" target-height="36" target-width="57.000008" target-x="105.6" target-y="54"/><path d="M 150.80 89.00 L 152.90 88.80 L 154.90 88.20 L 156.80 87.20 L 158.40 85.80 L 159.80 84.20 L 160.80 82.40 L 161.40 80.40 L 161.60 78.20 L 161.30 75.70 L 160.50 73.40 L 159.10 71.40 L 157.40 69.70 L 155.20 68.40 L 151.20 67.30 L 151.00 63.60 L 150.30 61.60 L 149.30 59.80 L 148.00 58.10 L 146.30 56.80 L 144.50 55.80 L 142.50 55.20 L 140.30 55.00 L 138.30 55.20 L 134.70 56.60 L 131.90 59.10 L 130.00 62.20 L 126.80 61.40 L 125.10 61.20 L 123.10 61.40 L 119.50 62.80 L 116.60 65.30 L 115.10 67.70 L 112.70 68.50 L 109.90 70.50 L 107.60 73.70 L 106.90 75.90 L 106.60 78.20 L 106.80 80.40 L 107.40 82.40 L 108.40 84.20 L 109.80 85.80 L 111.40 87.20 L 113.30 88.20 L 115.30 88.80 L 150.80 89.00 M 150.80 91.00 L 117.40 91.00 L 115.10 90.80 L 113.00 90.20 L 109.20 88.00 L 106.40 84.70 L 105.40 82.70 L 104.60 78.20 L 104.90 75.40 L 105.80 72.80 L 107.20 70.50 L 109.00 68.60 L 111.20 67.00 L 113.80 66.00 L 115.00 64.10 L 118.40 61.10 L 120.40 60.10 L 122.60 59.50 L 125.10 59.20 L 129.00 59.80 L 130.20 57.90 L 131.80 56.30 L 133.60 54.90 L 135.70 53.90 L 137.90 53.20 L 140.30 53.00 L 144.80 53.80 L 148.60 56.00 L 151.40 59.30 L 152.40 61.20 L 153.20 65.70 L 155.10 66.20 L 158.50 68.00 L 161.20 70.80 L 163.00 74.30 L 163.60 78.20 L 163.40 80.60 L 162.80 82.70 L 160.60 86.50 L 157.20 89.30 L 155.30 90.20 L 150.80 91.00 Z" fill="#c6c7c6" fill-rule="nonzero" group-id="2,3,43" node-id="118" stroke="none" target-height="38" target-width="59.000008" target-x="104.6" target-y="53"/></g><g node-id="332"><path d="M 333.50 152.00 L 285.50 152.00 L 280.90 151.40 L 276.80 149.70 L 273.10 146.90 L 270.30 143.20 L 268.60 139.10 L 268.00 134.50 L 268.20 131.60 L 268.90 128.90 L 270.00 126.40 L 271.50 124.00 L 273.40 121.90 L 275.50 120.20 L 277.90 118.80 L 280.90 117.60 L 282.80 114.60 L 285.00 112.30 L 287.50 110.50 L 290.30 109.10 L 293.30 108.30 L 296.50 108.00 L 299.20 108.20 L 302.60 109.10 L 304.70 105.70 L 306.80 103.50 L 309.30 101.60 L 312.20 100.20 L 315.30 99.30 L 318.50 99.00 L 320.80 99.20 L 325.20 100.30 L 329.10 102.60 L 330.80 104.10 L 332.40 105.80 L 334.60 109.70 L 335.80 114.00 L 336.00 117.20 L 339.50 118.10 L 341.90 119.20 L 344.10 120.60 L 347.80 124.40 L 350.20 129.10 L 350.80 131.70 L 350.80 136.80 L 349.70 141.20 L 347.40 145.10 L 345.90 146.90 L 342.20 149.70 L 338.10 151.40 L 333.50 152.00 Z" fill="#ececec" fill-rule="nonzero" group-id="2,3,44" node-id="122" stroke="none" target-height="53" target-width="82.79999" target-x="268" target-y="99"/><path d="M 333.50 151.00 L 336.80 150.70 L 339.80 149.80 L 342.60 148.30 L 345.20 146.20 L 347.20 143.70 L 348.80 140.80 L 349.70 137.80 L 350.00 134.50 L 349.20 129.40 L 347.00 125.00 L 343.50 121.40 L 339.20 119.00 L 335.00 118.00 L 334.70 113.10 L 333.70 110.10 L 332.20 107.30 L 330.10 104.80 L 327.60 102.70 L 324.80 101.20 L 321.70 100.30 L 318.50 100.00 L 315.50 100.30 L 312.60 101.10 L 309.90 102.40 L 307.50 104.20 L 305.50 106.30 L 303.10 110.30 L 299.10 109.20 L 296.50 109.00 L 293.50 109.30 L 290.70 110.10 L 288.00 111.40 L 285.60 113.10 L 283.60 115.20 L 281.60 118.50 L 278.30 119.70 L 276.10 121.00 L 274.00 122.60 L 272.30 124.60 L 270.90 126.90 L 269.80 129.30 L 269.20 131.80 L 269.00 134.50 L 269.30 137.80 L 270.20 140.80 L 271.80 143.70 L 273.80 146.20 L 276.40 148.30 L 279.20 149.80 L 282.20 150.70 L 285.50 151.00 L 333.50 151.00 M 333.50 153.00 L 285.50 153.00 L 282.10 152.70 L 279.00 151.90 L 276.20 150.50 L 273.60 148.60 L 271.40 146.40 L 269.50 143.80 L 268.20 141.00 L 267.30 137.90 L 267.00 134.50 L 267.80 129.10 L 270.00 124.40 L 273.40 120.50 L 277.70 117.70 L 280.20 116.80 L 282.00 114.00 L 284.20 111.70 L 286.90 109.70 L 289.80 108.30 L 293.00 107.30 L 296.50 107.00 L 299.40 107.20 L 302.10 107.90 L 303.90 105.10 L 306.20 102.70 L 308.80 100.70 L 311.80 99.30 L 315.00 98.40 L 318.50 98.00 L 321.90 98.30 L 324.90 99.20 L 327.80 100.50 L 330.40 102.30 L 332.60 104.50 L 334.40 107.10 L 335.80 109.90 L 336.70 113.00 L 337.00 116.30 L 339.80 117.10 L 342.30 118.30 L 344.70 119.80 L 346.80 121.60 L 348.50 123.70 L 350.00 126.20 L 351.10 128.80 L 351.80 131.50 L 352.00 134.50 L 351.70 137.90 L 350.80 141.00 L 349.50 143.80 L 347.60 146.40 L 345.40 148.60 L 342.80 150.50 L 340.00 151.90 L 336.90 152.70 L 333.50 153.00 Z" fill="#c6c7c6" fill-rule="nonzero" group-id="2,3,44" node-id="124" stroke="none" target-height="55" target-width="85" target-x="267" target-y="98"/></g><g node-id="333"><path d="M 146.40 213.80 L 146.10 210.30 L 146.20 207.90 L 146.70 205.50 L 147.70 203.00 L 149.30 200.70 L 151.00 198.90 L 152.90 197.50 L 156.30 195.80 L 156.70 199.60 L 156.50 201.90 L 156.00 204.40 L 155.00 206.90 L 153.50 209.10 L 151.70 210.90 L 149.80 212.30 L 146.40 214.10 Z M 155.90 196.40 L 153.90 197.50 L 150.90 199.70 L 148.10 203.20 L 146.80 207.40 L 146.60 211.10 L 146.80 213.40 L 148.80 212.40 L 151.80 210.10 L 154.60 206.70 L 156.00 202.40 L 156.20 198.70 L 155.90 196.40 Z" fill="#f1f1f1" fill-rule="nonzero" group-id="2,3,45" id="路径_8429" node-id="23" stroke="none" target-height="18.300003" target-width="10.599991" target-x="146.1" target-y="195.8"/></g><path d="M 153.00 205.20 L 150.80 206.80 L 149.20 208.60 L 147.90 210.60 L 146.40 213.70 L 149.90 213.90 L 154.60 213.00 L 157.00 211.90 L 159.20 210.20 L 162.20 206.50 L 163.60 203.40 L 160.20 203.20 L 157.90 203.40 L 155.50 204.00 L 153.00 205.20 Z" fill="#f1f1f1" fill-rule="nonzero" group-id="2,3,46" id="路径_8430" node-id="24" stroke="none" target-height="10.699997" target-width="17.200012" target-x="146.4" target-y="203.2"/></g><g node-id="292"><path d="M 283.00 90.30 L 282.80 95.90 L 282.10 101.40 L 281.00 106.70 L 279.50 111.80 L 277.60 116.90 L 275.30 121.60 L 272.70 126.20 L 269.80 130.60 L 262.90 138.50 L 255.00 145.30 L 250.60 148.30 L 246.00 150.90 L 241.20 153.10 L 236.20 155.00 L 231.00 156.50 L 225.70 157.60 L 220.20 158.30 L 214.50 158.50 L 208.80 158.30 L 203.30 157.60 L 198.00 156.50 L 192.80 155.00 L 187.80 153.10 L 183.00 150.90 L 178.40 148.30 L 174.00 145.30 L 169.90 142.10 L 162.50 134.70 L 159.20 130.60 L 156.30 126.20 L 153.70 121.60 L 151.40 116.90 L 149.50 111.80 L 148.00 106.70 L 146.90 101.40 L 146.20 95.90 L 146.00 90.30 L 146.20 84.60 L 146.90 79.10 L 148.00 73.80 L 149.50 68.70 L 151.40 63.60 L 153.70 58.90 L 156.30 54.30 L 159.20 49.90 L 162.50 45.80 L 169.90 38.40 L 174.00 35.20 L 178.40 32.20 L 183.00 29.60 L 187.80 27.40 L 192.80 25.50 L 198.00 24.00 L 203.30 22.90 L 208.80 22.20 L 214.50 22.00 L 220.20 22.20 L 225.70 22.90 L 231.00 24.00 L 236.20 25.50 L 241.20 27.40 L 246.00 29.60 L 250.60 32.20 L 255.00 35.20 L 262.90 42.00 L 269.80 49.90 L 272.70 54.30 L 275.30 58.90 L 277.60 63.60 L 279.50 68.70 L 281.00 73.80 L 282.10 79.10 L 282.80 84.60 L 283.00 90.30 Z" fill="#ffffff" fill-rule="nonzero" group-id="2,4" node-id="137" stroke="none" target-height="136.5" target-width="137" target-x="146" target-y="22"/><path d="M 282.00 90.30 L 281.80 95.80 L 281.10 101.20 L 280.00 106.40 L 278.60 111.50 L 276.70 116.50 L 274.50 121.20 L 271.90 125.70 L 269.00 130.00 L 262.20 137.80 L 254.40 144.50 L 250.10 147.40 L 245.50 150.00 L 240.80 152.20 L 235.80 154.10 L 230.80 155.60 L 225.50 156.60 L 220.10 157.30 L 214.50 157.50 L 208.90 157.30 L 203.50 156.60 L 198.20 155.60 L 193.20 154.10 L 188.20 152.20 L 183.50 150.00 L 178.90 147.40 L 170.60 141.30 L 163.30 134.00 L 160.00 130.00 L 157.10 125.70 L 154.50 121.20 L 152.30 116.50 L 150.40 111.50 L 149.00 106.40 L 147.90 101.20 L 147.20 95.80 L 147.00 90.30 L 147.20 84.70 L 147.90 79.30 L 149.00 74.10 L 150.40 69.00 L 152.30 64.00 L 154.50 59.30 L 157.10 54.80 L 163.30 46.50 L 170.60 39.20 L 174.60 36.00 L 178.90 33.10 L 183.50 30.50 L 188.20 28.30 L 193.20 26.40 L 198.20 24.90 L 203.50 23.90 L 208.90 23.20 L 214.50 23.00 L 220.10 23.20 L 225.50 23.90 L 230.80 24.90 L 235.80 26.40 L 240.80 28.30 L 245.50 30.50 L 250.10 33.10 L 254.40 36.00 L 262.20 42.70 L 269.00 50.50 L 271.90 54.80 L 274.50 59.30 L 276.70 64.00 L 278.60 69.00 L 280.00 74.10 L 281.10 79.30 L 281.80 84.70 L 282.00 90.30 Z" fill="none" group-id="2,4" node-id="139" stroke="#d8d8d8" stroke-linecap="butt" stroke-width="2" target-height="134.5" target-width="135" target-x="147" target-y="23"/></g><g node-id="293"><path d="M 211.10 151.80 L 222.00 151.80 L 222.00 168.00 L 211.10 168.00 Z" fill="#ffffff" fill-rule="nonzero" group-id="2,5" node-id="143" stroke="none" target-height="16.199997" target-width="10.899994" target-x="211.1" target-y="151.8"/><path d="M 212.10 152.80 L 221.00 152.80 L 221.00 167.00 L 212.10 167.00 Z" fill="none" group-id="2,5" node-id="145" stroke="#d8d8d8" stroke-linecap="butt" stroke-width="2" target-height="14.199997" target-width="8.899994" target-x="212.1" target-y="152.8"/></g><g node-id="294"><path d="M 270.00 89.50 L 269.30 98.70 L 267.10 107.30 L 265.00 112.80 L 262.40 118.00 L 259.20 122.90 L 255.60 127.30 L 251.50 131.40 L 247.10 135.10 L 242.30 138.30 L 237.20 140.90 L 231.70 143.10 L 227.50 144.30 L 218.60 145.80 L 214.00 146.00 L 204.90 145.20 L 196.30 143.10 L 190.80 140.90 L 185.70 138.30 L 180.90 135.10 L 176.50 131.40 L 172.40 127.30 L 168.80 122.90 L 165.60 118.00 L 163.00 112.80 L 160.90 107.30 L 159.60 103.10 L 158.20 94.20 L 158.20 84.80 L 158.70 80.30 L 160.90 71.60 L 163.00 66.10 L 165.60 61.00 L 168.80 56.10 L 172.40 51.60 L 176.50 47.50 L 180.90 43.90 L 185.70 40.70 L 190.80 38.00 L 196.30 35.90 L 200.50 34.60 L 209.40 33.20 L 214.00 33.00 L 218.70 33.20 L 227.50 34.60 L 231.70 35.90 L 237.20 38.00 L 242.30 40.70 L 247.10 43.90 L 251.50 47.50 L 255.60 51.60 L 259.20 56.10 L 262.40 61.00 L 265.00 66.10 L 267.10 71.60 L 269.30 80.30 L 270.00 89.50 Z" fill="#ffffff" fill-rule="nonzero" group-id="2,6" node-id="149" stroke="none" target-height="113" target-width="111.8" target-x="158.2" target-y="33"/><path d="M 269.00 89.50 L 268.70 95.60 L 267.70 101.40 L 266.20 107.00 L 264.10 112.40 L 261.50 117.50 L 258.40 122.30 L 254.80 126.70 L 250.90 130.70 L 246.50 134.30 L 241.80 137.40 L 236.70 140.00 L 231.40 142.20 L 225.80 143.70 L 220.10 144.60 L 214.00 145.00 L 207.90 144.60 L 202.20 143.70 L 196.60 142.20 L 191.30 140.00 L 186.20 137.40 L 181.50 134.30 L 177.10 130.70 L 173.20 126.70 L 169.60 122.30 L 166.50 117.50 L 163.90 112.40 L 161.80 107.00 L 160.30 101.40 L 159.30 95.60 L 159.00 89.50 L 159.30 83.40 L 160.30 77.50 L 161.80 71.90 L 163.90 66.50 L 166.50 61.50 L 169.60 56.70 L 173.20 52.30 L 177.10 48.30 L 181.50 44.70 L 186.20 41.60 L 191.30 38.90 L 196.60 36.80 L 202.20 35.30 L 207.90 34.30 L 214.00 34.00 L 220.10 34.30 L 225.80 35.30 L 231.40 36.80 L 236.70 38.90 L 241.80 41.60 L 246.50 44.70 L 250.90 48.30 L 254.80 52.30 L 258.40 56.70 L 261.50 61.50 L 264.10 66.50 L 266.20 71.90 L 267.70 77.50 L 268.70 83.40 L 269.00 89.50 Z" fill="none" group-id="2,6" node-id="151" stroke="#d8d8d8" stroke-linecap="butt" stroke-width="2" target-height="111" target-width="110" target-x="159" target-y="34"/></g><g node-id="295"><path d="M 257.30 118.80 L 174.50 118.80 L 172.90 118.60 L 171.50 118.00 L 169.30 115.80 L 168.70 114.50 L 168.50 112.80 L 168.50 75.90 L 168.70 74.20 L 169.30 72.80 L 171.50 70.70 L 172.90 70.10 L 174.50 69.90 L 257.30 69.90 L 258.90 70.10 L 260.30 70.70 L 262.40 72.80 L 263.00 74.20 L 263.30 75.90 L 263.30 112.80 L 263.00 114.50 L 262.40 115.80 L 261.50 117.10 L 260.30 118.00 L 258.90 118.60 L 257.30 118.80 Z" fill="#fff9ef" fill-opacity="0.89" fill-rule="nonzero" group-id="2,7" node-id="155" stroke="none" target-height="48.9" target-width="94.79999" target-x="168.5" target-y="69.9"/><path d="M 257.30 117.80 L 174.50 117.80 L 172.00 117.10 L 170.20 115.30 L 169.50 112.80 L 169.50 75.90 L 170.20 73.30 L 172.00 71.50 L 173.10 71.10 L 257.30 70.90 L 259.80 71.50 L 261.60 73.30 L 262.30 75.90 L 262.30 112.80 L 262.10 114.20 L 260.80 116.40 L 258.60 117.60 L 257.30 117.80 Z" fill="none" group-id="2,7" node-id="157" stroke="#c6c7c6" stroke-dasharray="4 4" stroke-linecap="butt" stroke-opacity="0.89" stroke-width="2" target-height="46.9" target-width="92.79999" target-x="169.5" target-y="70.9"/></g><g node-id="296"><path d="M 195.90 81.50 L 196.10 80.30 L 196.80 79.40 L 197.70 78.70 L 198.90 78.50 L 200.10 78.70 L 201.00 79.40 L 201.60 80.30 L 201.90 81.50 L 201.60 82.70 L 201.00 83.60 L 200.10 84.20 L 198.90 84.50 L 197.70 84.20 L 196.80 83.60 L 196.10 82.70 L 195.90 81.50 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,8" id="椭圆_659" node-id="37" stroke="none" target-height="6" target-width="6" target-x="195.9" target-y="78.5"/></g><g node-id="297"><path d="M 187.90 81.50 L 188.10 80.30 L 188.80 79.40 L 189.70 78.70 L 190.90 78.50 L 192.10 78.70 L 193.00 79.40 L 193.60 80.30 L 193.90 81.50 L 193.60 82.70 L 193.00 83.60 L 192.10 84.20 L 190.90 84.50 L 189.70 84.20 L 188.80 83.60 L 188.10 82.70 L 187.90 81.50 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,9" id="椭圆_660" node-id="38" stroke="none" target-height="6" target-width="6" target-x="187.9" target-y="78.5"/></g><g node-id="298"><path d="M 179.90 81.50 L 180.10 80.30 L 180.80 79.40 L 181.70 78.70 L 182.90 78.50 L 184.10 78.70 L 185.00 79.40 L 185.60 80.30 L 185.90 81.50 L 185.60 82.70 L 185.00 83.60 L 184.10 84.20 L 182.90 84.50 L 181.70 84.20 L 180.80 83.60 L 180.10 82.70 L 179.90 81.50 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,10" id="椭圆_661" node-id="39" stroke="none" target-height="6" target-width="6" target-x="179.9" target-y="78.5"/></g><g node-id="299"><path d="M 250.00 25.10 L 281.60 30.10 L 277.90 53.80 L 261.40 52.30 L 255.80 54.80 L 251.40 51.20 L 246.30 48.80 Z" fill="#ffffff" fill-rule="nonzero" group-id="2,11" id="路径_8516" node-id="40" stroke="none" target-height="29.699999" target-width="35.300003" target-x="246.3" target-y="25.1"/></g><g node-id="300"><path d="M 278.60 28.70 L 253.60 24.70 L 250.70 25.10 L 248.40 26.70 L 247.20 29.40 L 244.60 47.10 L 245.00 48.40 L 246.60 50.80 L 249.30 51.90 L 252.50 52.50 L 253.90 58.90 L 254.30 59.60 L 255.00 60.00 L 255.80 59.90 L 256.40 59.30 L 259.70 53.60 L 275.50 55.90 L 276.90 55.50 L 279.20 53.90 L 280.40 51.20 L 283.10 33.60 L 282.20 30.90 L 281.20 29.80 L 278.60 28.70 Z M 277.90 50.80 L 277.50 51.80 L 276.80 52.60 L 275.80 53.10 L 274.70 53.10 L 258.70 50.80 L 256.00 54.80 L 254.60 50.20 L 248.70 48.80 L 247.90 48.10 L 247.50 47.10 L 247.40 46.00 L 250.00 29.80 L 250.40 28.80 L 251.10 28.00 L 252.10 27.60 L 253.20 27.50 L 278.10 31.50 L 279.20 31.90 L 279.90 32.60 L 280.40 33.50 L 280.40 34.70 Z M 253.50 38.90 L 253.60 39.70 L 254.40 40.90 L 256.00 41.10 L 257.20 40.30 L 257.40 39.50 L 257.40 38.70 L 256.50 37.50 L 255.00 37.30 L 254.30 37.60 L 253.50 38.90 Z M 261.70 40.20 L 261.70 41.00 L 262.60 42.20 L 264.10 42.40 L 265.30 41.50 L 265.60 40.80 L 265.50 40.00 L 264.70 38.80 L 263.20 38.60 L 262.50 38.90 L 261.70 40.20 Z M 269.90 41.50 L 269.90 42.30 L 270.80 43.50 L 272.30 43.70 L 273.50 42.80 L 273.80 42.10 L 273.80 41.30 L 272.90 40.10 L 271.40 39.90 L 270.70 40.20 L 269.90 41.50 Z" fill="#d8d8d8" fill-rule="nonzero" group-id="2,12" id="icon" node-id="41" stroke="none" target-height="35.3" target-width="38.5" target-x="244.6" target-y="24.7"/></g><g node-id="301"><path d="M 208.70 177.60 L 172.70 177.50 L 172.10 176.50 L 172.10 164.60 L 172.40 163.80 L 173.10 163.50 L 209.10 163.60 L 209.70 164.60 L 209.70 176.50 L 209.40 177.30 L 208.70 177.60 Z" fill="#e6e5e5" fill-rule="nonzero" group-id="2,13" id="路径_8517" node-id="42" stroke="none" target-height="14.100006" target-width="37.59999" target-x="172.1" target-y="163.5"/></g><g node-id="302"><path d="M 208.70 207.30 L 172.70 207.10 L 172.10 205.10 L 172.10 181.20 L 172.40 179.70 L 173.10 179.10 L 209.10 179.20 L 209.70 181.20 L 209.70 205.10 L 209.40 206.60 L 208.70 207.30 Z" fill="#e6e5e5" fill-rule="nonzero" group-id="2,14" id="路径_8533" node-id="43" stroke="none" target-height="28.199997" target-width="37.59999" target-x="172.1" target-y="179.1"/></g><g node-id="303"><path d="M 123.20 201.80 L 124.00 202.00 L 125.60 201.70 L 127.20 200.10 L 127.80 198.80 L 128.90 193.20 L 125.30 195.80 L 123.80 197.40 L 122.90 199.50 L 123.20 201.70" fill="#e6e6e6" fill-rule="nonzero" group-id="2,15" id="Path_438" node-id="44" stroke="none" target-height="8.800003" target-width="5.9999924" target-x="122.9" target-y="193.2"/></g><g node-id="304"><path d="M 123.50 207.20 L 123.20 202.30 L 123.60 200.20 L 124.60 198.40 L 126.30 196.80 L 126.50 197.10 L 125.00 198.40 L 124.00 200.10 L 123.50 202.20 L 123.80 207.10 L 123.50 207.20 Z" fill="#f2f2f2" fill-rule="nonzero" group-id="2,16" id="Path_439" node-id="45" stroke="none" target-height="10.399994" target-width="3.300003" target-x="123.2" target-y="196.8"/></g><g node-id="305"><path d="M 125.00 204.60 L 125.90 205.40 L 127.10 205.70 L 128.60 205.20 L 129.90 204.20 L 132.20 202.10 L 129.00 202.00 L 126.50 202.60 L 125.40 203.80 L 125.10 204.60" fill="#e6e6e6" fill-rule="nonzero" group-id="2,17" id="Path_442" node-id="46" stroke="none" target-height="3.699997" target-width="7.199997" target-x="125" target-y="202"/></g><g node-id="306"><path d="M 122.80 208.10 L 124.70 205.30 L 125.80 204.20 L 127.30 203.50 L 129.30 203.50 L 127.60 203.70 L 126.10 204.40 L 125.00 205.40 L 123.10 208.20 L 122.80 208.10 Z" fill="#f2f2f2" fill-rule="nonzero" group-id="2,18" id="Path_443" node-id="47" stroke="none" target-height="4.699997" target-width="6.5" target-x="122.8" target-y="203.5"/></g><g node-id="307"><path d="M 228.80 204.00 L 227.70 204.60 L 226.50 204.60 L 225.20 203.70 L 224.20 202.40 L 222.50 199.80 L 225.60 200.50 L 227.80 201.70 L 228.60 203.20 L 228.80 204.00" fill="#e6e6e6" fill-rule="nonzero" group-id="2,19" id="Path_442-2" node-id="48" stroke="none" target-height="4.800003" target-width="6.300003" target-x="222.5" target-y="199.8"/></g><g node-id="308"><path d="M 230.00 208.00 L 229.00 204.80 L 228.10 203.50 L 226.90 202.40 L 225.00 201.80 L 226.60 202.60 L 227.80 203.60 L 228.60 204.80 L 229.70 208.00 L 230.00 208.00 Z" fill="#f2f2f2" fill-rule="nonzero" group-id="2,20" id="Path_443-2" node-id="49" stroke="none" target-height="6.199997" target-width="5" target-x="225" target-y="201.8"/></g><g node-id="309"><path d="M 177.60 166.70 L 187.00 166.70 L 187.00 167.80 L 177.60 167.80 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,21" id="矩形_2809" node-id="50" stroke="none" target-height="1.1000061" target-width="9.399994" target-x="177.6" target-y="166.7"/></g><g node-id="310"><path d="M 200.10 167.30 L 199.50 168.00 L 198.80 167.30 L 199.50 166.70 L 200.10 167.30 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,22" id="椭圆_666" node-id="51" stroke="none" target-height="1.300003" target-width="1.300003" target-x="198.8" target-y="166.7"/></g><g node-id="311"><path d="M 202.20 167.30 L 201.60 168.00 L 201.10 167.80 L 201.00 167.30 L 201.60 166.70 L 202.20 167.30 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,23" id="椭圆_667" node-id="52" stroke="none" target-height="1.300003" target-width="1.199997" target-x="201" target-y="166.7"/></g><g node-id="312"><path d="M 204.40 167.30 L 203.70 168.00 L 203.30 167.80 L 203.10 167.30 L 203.70 166.70 L 204.40 167.30 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,24" id="椭圆_668" node-id="53" stroke="none" target-height="1.300003" target-width="1.2999878" target-x="203.1" target-y="166.7"/></g><g node-id="313"><path d="M 195.30 151.80 L 194.60 151.90 L 186.60 162.60 L 185.70 162.60 L 185.50 162.20 L 185.00 162.20 L 184.80 162.60 L 184.30 162.20 L 183.80 162.20 L 183.60 162.60 L 183.10 162.20 L 182.50 162.20 L 182.40 162.60 L 181.90 162.20 L 181.30 162.20 L 181.10 162.60 L 180.70 162.20 L 180.10 162.20 L 179.90 162.60 L 179.40 162.20 L 178.90 162.20 L 178.70 162.60 L 178.20 162.20 L 177.70 162.20 L 177.50 162.60 L 177.00 162.20 L 176.50 162.20 L 176.30 162.60 L 175.30 162.20 L 174.80 162.60 L 174.60 162.20 L 174.10 162.20 L 173.90 162.60 L 173.20 162.80 L 173.20 163.90 L 186.90 163.90 L 195.40 152.50 L 195.30 151.80 Z" fill="#01cc83" fill-rule="nonzero" group-id="2,25" id="路径_8520" node-id="54" stroke="none" target-height="12.099991" target-width="22.199997" target-x="173.2" target-y="151.8"/></g><g node-id="314"><path d="M 144.70 203.90 L 146.30 204.80 L 150.30 198.90 L 147.90 197.70 Z" fill="#ffb7b7" fill-rule="nonzero" group-id="2,26" id="路径_8521" node-id="55" stroke="none" target-height="7.100006" target-width="5.600006" target-x="144.7" target-y="197.7"/></g><g node-id="315"><path d="M 144.60 203.20 L 148.50 205.40 L 149.00 207.00 L 148.80 207.90 L 143.50 205.30 Z" fill="#2f2e41" fill-rule="nonzero" group-id="2,27" id="路径_8522" node-id="56" stroke="none" target-height="4.699997" target-width="5.5" target-x="143.5" target-y="203.2"/></g><g node-id="316"><path d="M 163.40 206.20 L 165.20 206.20 L 166.10 199.20 L 163.40 199.20 Z" fill="#ffb7b7" fill-rule="nonzero" group-id="2,28" id="路径_8523" node-id="57" stroke="none" target-height="7" target-width="2.7000122" target-x="163.4" target-y="199.2"/></g><g node-id="317"><path d="M 162.90 205.60 L 167.40 205.80 L 168.60 207.00 L 168.80 207.90 L 162.90 208.00 Z" fill="#2f2e41" fill-rule="nonzero" group-id="2,29" id="路径_8524" node-id="58" stroke="none" target-height="2.399994" target-width="5.900009" target-x="162.9" target-y="205.6"/></g><g node-id="318"><path d="M 154.90 149.10 L 154.30 148.90 L 153.80 149.50 L 153.50 158.00 L 155.60 165.10 L 156.90 162.80 L 156.40 157.80 Z" fill="#fe8f29" fill-rule="nonzero" group-id="2,30" id="路径_8525" node-id="59" stroke="none" target-height="16.200012" target-width="3.399994" target-x="153.5" target-y="148.9"/></g><g node-id="319"><path d="M 167.90 169.60 L 168.40 176.40 L 167.50 182.20 L 166.50 203.80 L 162.90 203.50 L 161.60 187.50 L 160.40 179.50 L 157.90 186.80 L 149.50 202.20 L 145.70 199.20 L 148.20 193.00 L 150.60 188.30 L 153.10 185.10 L 154.70 167.00 Z" fill="#2f2e41" fill-rule="nonzero" group-id="2,31" id="路径_8526" node-id="60" stroke="none" target-height="36.800003" target-width="22.699997" target-x="145.7" target-y="167"/></g><g node-id="320"><path d="M 165.60 132.20 L 166.80 133.20 L 167.60 134.60 L 167.70 136.20 L 167.20 137.80 L 166.20 139.00 L 164.80 139.70 L 163.20 139.90 L 161.60 139.40 L 160.40 138.30 L 159.60 137.00 L 159.50 135.40 L 160.00 133.80 L 161.10 132.50 L 162.40 131.80 L 164.00 131.70 L 165.60 132.20 Z" fill="#ffb7b7" fill-rule="nonzero" group-id="2,32" id="椭圆_675" node-id="61" stroke="none" target-height="8.199997" target-width="8.199997" target-x="159.5" target-y="131.7"/></g><g node-id="321"><path d="M 163.30 136.70 L 164.00 136.40 L 165.10 134.50 L 167.10 134.40 L 168.00 133.80 L 168.40 132.70 L 167.80 130.50 L 167.70 131.40 L 167.50 130.50 L 167.00 129.90 L 167.10 131.20 L 166.50 130.30 L 165.50 130.00 L 165.50 130.80 L 161.80 130.90 L 160.00 132.10 L 159.40 133.10 L 159.20 135.20 L 159.70 137.10 L 160.70 139.40 L 161.10 139.60 L 161.80 139.10 L 161.70 136.90 L 161.90 136.30 L 162.50 136.00 L 163.10 136.20 L 163.20 136.80 Z" fill="#2f2e41" fill-rule="nonzero" group-id="2,33" id="路径_8527" node-id="62" stroke="none" target-height="9.700012" target-width="9.199997" target-x="159.2" target-y="129.9"/></g><g node-id="322"><path d="M 168.10 171.50 L 154.40 170.60 L 155.40 166.30 L 168.00 169.10 Z" fill="#cbcbcb" fill-rule="nonzero" group-id="2,34" id="路径_8528" node-id="63" stroke="none" target-height="5.199997" target-width="13.700012" target-x="154.4" target-y="166.3"/></g><g node-id="323"><path d="M 159.70 141.40 L 160.50 140.20 L 164.10 141.80 L 168.70 170.60 L 158.40 170.20 L 157.60 168.50 L 156.70 170.10 L 154.60 170.10 L 152.40 168.80 L 154.50 162.10 L 155.20 156.10 L 154.20 150.30 L 154.20 147.10 L 155.50 144.30 L 158.10 142.20 Z" fill="#fe8f29" fill-rule="nonzero" group-id="2,35" id="路径_8529" node-id="64" stroke="none" target-height="30.40001" target-width="16.300003" target-x="152.4" target-y="140.2"/></g><g node-id="324"><path d="M 178.00 162.30 L 176.90 162.10 L 176.30 161.00 L 171.50 159.70 L 173.40 158.00 L 178.60 159.90 L 179.10 161.30 L 178.00 162.30 Z" fill="#ffb7b7" fill-rule="nonzero" group-id="2,36" id="路径_8530" node-id="65" stroke="none" target-height="4.300003" target-width="7.600006" target-x="171.5" target-y="158"/></g><g node-id="325"><path d="M 175.90 161.60 L 175.20 161.60 L 167.20 158.60 L 165.40 157.70 L 163.90 156.40 L 158.80 147.90 L 158.90 145.90 L 159.60 145.10 L 160.50 144.50 L 161.50 144.40 L 162.50 144.70 L 163.30 145.30 L 169.10 154.40 L 176.30 158.60 L 176.60 159.50 L 175.90 161.60 Z" fill="#fe8f29" fill-rule="nonzero" group-id="2,37" id="路径_8531" node-id="66" stroke="none" target-height="17.200012" target-width="17.800003" target-x="158.8" target-y="144.4"/></g><g node-id="326"><path d="M 237.30 208.30 L 110.50 208.30 L 110.50 208.00 L 237.30 208.00 L 237.30 208.30 Z" fill="#cbcbcb" fill-rule="nonzero" group-id="2,38" id="路径_8532" node-id="67" stroke="none" target-height="0.30000305" target-width="126.8" target-x="110.5" target-y="208"/></g><g node-id="327"><path d="M 213.00 166.00 L 221.60 166.20 L 223.00 166.80 L 224.20 167.70 L 225.20 169.00 L 225.80 170.40 L 226.00 172.00 L 226.00 199.00 L 225.80 200.60 L 225.20 202.00 L 223.00 204.20 L 221.60 204.80 L 213.00 205.00 L 211.40 204.80 L 210.00 204.20 L 208.80 203.20 L 207.80 202.00 L 207.20 200.60 L 207.00 199.00 L 207.00 172.00 L 207.20 170.40 L 207.80 169.00 L 210.00 166.80 L 211.40 166.20 L 213.00 166.00 Z" fill="#fe8f29" fill-rule="nonzero" group-id="2,39" node-id="285" stroke="none" target-height="39" target-width="19" target-x="207" target-y="166"/><path d="M 213.00 166.50 L 221.50 166.70 L 223.90 168.10 L 225.30 170.50 L 225.50 172.00 L 225.50 199.00 L 225.30 200.50 L 224.80 201.80 L 222.80 203.70 L 220.00 204.50 L 211.50 204.30 L 209.10 202.90 L 207.70 200.50 L 207.50 199.00 L 207.50 172.00 L 207.70 170.50 L 208.20 169.20 L 210.20 167.20 L 213.00 166.50 Z" fill="none" group-id="2,39" node-id="287" stroke="#8e8e8e" stroke-linecap="butt" stroke-width="1" target-height="38" target-width="18" target-x="207.5" target-y="166.5"/></g></g></svg>
        </div>
        <div class="empty-text">未搜索到相关结果</div>
      </div>

          <!-- 底线提示 -->
        <div v-if="searchResults.length > 0 && !hasMore" class="bottom-line">
          <div class="line"></div>
          <div class="text">小哈是有底线的</div>
          <div class="line"></div>
      </div>
    </div>

    <!-- 笔记详情模态框 -->
    <NoteDetailModal 
      v-model:visible="showModal"
      :note="selectedNote"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import NoteCard from '@/components/note/NoteCard.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import NoteDetailModal from '@/components/note/NoteDetailModal.vue'
import { onClickOutside } from '@vueuse/core'
import { searchNote, searchUser } from '@/api/search'
import { followUser } from '@/api/relation'
import UserCard from '@/components/user/UserCard.vue'
import { message } from '@/utils/message'

const route = useRoute()
const activeTab = ref('notes') // 默认选中笔记标签
const showModal = ref(false)
const selectedNote = ref(null)



// 筛选相关状态
const showFilter = ref(false)
const filterRef = ref(null)
const selectedTime = ref(null)
const selectedSort = ref(null)
const selectedType = ref(null)

const handleTabChange = (type) => {
  console.log('tab 切换了：' + type)
  selectedType.value = type
  if (type === 2) {
    activeTab.value = 'users'
  } else {
    activeTab.value = 'others'
  }
  console.log('当前 tab：' + activeTab.value)
  performSearch(true)
}

const categories = [
  { name: '全部', type: null },
  { name: '图文', type: 0 },
  { name: '视频', type: 1 },
  { name: '用户', type: 2 },
]

// 排序方式选项
const sortOptions = [
  { label: '综合', value: null },
  { label: '最新', value: 0 },
  { label: '最多点赞', value: 1 },
  { label: '最多收藏', value: 2 },
  { label: '最多评论', value: 3 }
]

// 笔记类型选项
const noteTypes = [
  { label: '不限', value: null },
  { label: '图文', value: 0 },
  { label: '视频', value: 1 },
]

// 时间筛选选项
const timeFilters = [
  { label: '不限', value: null },
  { label: '一天内', value: 0 },
  { label: '一周内', value: 1 },
  { label: '半年内', value: 2 }
]

// 使用 vueuse 的 onClickOutside
onClickOutside(filterRef, () => {
  showFilter.value = false
})

// 重置筛选
const resetFilters = () => {
  selectedTime.value = null
  selectedSort.value = null
  selectedType.value = null
}

// 应用筛选
const applyFilters = () => {
  // TODO: 应用筛选条件
  console.log('应用筛选:', {
    time: selectedTime.value,
    sort: selectedSort.value,
    type: selectedType.value
  })
  showFilter.value = false
  performSearch(true)
}

// 从路由中获取搜索关键词
const keyword = computed(() => route.query.keyword || '')

const searchResults = ref([])
const isLoading = ref(false)
const hasMore = ref(true)
const currPageNo = ref(1)

const loadingRef = ref(null)

// 执行搜索
const performSearch = (isFirstPage = true) => {
  if (isLoading.value) return

  isLoading.value = true
  
  // 如果是第一页，重置数据
  if (isFirstPage) {
    // loadingRef.value.show()
    searchResults.value = []
    currPageNo.value = 1
    hasMore.value = true
  }
  
  // 根据当前选中的标签决定调用哪个搜索 API
  if (activeTab.value === 'users') {
    // 用户搜索
    searchUser(
      keyword.value, 
      currPageNo.value
    ).then(res => {
      if (res.success) {
        const newResults = res.data || []
        
        // 检查是否有重复数据
        const existingIds = searchResults.value.map(item => item.id)
        const uniqueNewResults = newResults.filter(item => !existingIds.includes(item.id))
        
        // 添加不重复的数据
        if (uniqueNewResults.length > 0) {
          searchResults.value = [...searchResults.value, ...uniqueNewResults]
          currPageNo.value++
        }
        
        // 判断是否还有更多数据
        hasMore.value = newResults.length > 0 && newResults.length === 20
      } else {
        hasMore.value = false
      }
    }).finally(() => {
      isLoading.value = false
      if (isFirstPage) {
        loadingRef.value.hide()
      }
    })
  } else {
    // // 笔记搜索 - 根据不同的标签设置不同的类型
    // let noteType = null
    // if (activeTab.value === 'images') {
    //   noteType = 0 // 图文类型
    // } else if (activeTab.value === 'videos') {
    //   noteType = 1 // 视频类型
    // }
    // 'all' 或其他情况保持 null，表示搜索所有类型
    console.log('执行搜索笔记')
    searchNote(
      keyword.value, 
      selectedType.value, 
      selectedSort.value, 
      selectedTime.value, 
      currPageNo.value
    ).then(res => {
      if (res.success) {
        const newResults = res.data || []
        
        // 检查是否有重复数据
        const existingIds = searchResults.value.map(item => item.id)
        const uniqueNewResults = newResults.filter(item => !existingIds.includes(item.id))
        
        // 添加不重复的数据
        if (uniqueNewResults.length > 0) {
          searchResults.value = [...searchResults.value, ...uniqueNewResults]
          currPageNo.value++
        }
        
        // 判断是否还有更多数据
        hasMore.value = newResults.length > 0 && newResults.length === 20
      } else {
        hasMore.value = false
      }
    }).finally(() => {
      isLoading.value = false
      if (isFirstPage) {
        loadingRef.value.hide()
      }
    })
  }
}

// 监听路由参数变化，当搜索关键词变化时重新搜索
watch(() => route.query.keyword, (newKeyword, oldKeyword) => {
  if (newKeyword !== oldKeyword) {
    console.log('搜索关键词变化，重新搜索:', newKeyword)
    performSearch(true) // 重置并执行新搜索
  }
}, { immediate: true })

// 监听 activeTab 变化
watch(activeTab, () => {
  // 切换标签时重置并重新搜索
  performSearch(true)
})

// 加载更多结果
const loadMore = () => {
  if (!hasMore.value || isLoading.value) return
  performSearch(false)
}

// 处理滚动加载
const handleScroll = () => {
  if (isLoading.value || !hasMore.value) return
  
  const scrollTop = window.pageYOffset || document.documentElement.scrollTop
  const windowHeight = window.innerHeight
  const documentHeight = document.documentElement.scrollHeight
  
  // 当滚动到距离底部一定距离时加载更多
  if (documentHeight - scrollTop - windowHeight < 200) {
    loadMore()
  }
}

// 组件挂载和卸载时添加/移除滚动事件监听
onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})


// 笔记类型
const type = ref(null)
const sort = ref(null)
const publishTimeRange = ref(null)

searchNote(keyword.value, type.value, sort.value, publishTimeRange.value, currPageNo.value).then(res => {
  if (res.success) {
    searchResults.value = res.data
  }
})

// 点击笔记卡片
const onNoteClick = (note) => {
  selectedNote.value = note
  showModal.value = true
}

onMounted(() => {
  // 获取搜索关键词
  const keyword = route.query.keyword
  // TODO: 根据关键词获取搜索结果
  console.log('搜索关键词:', keyword)
})

// 处理用户关注事件
const handleFollowUser = (userId) => {
  console.log('关注用户:', userId)
  // TODO: 调用关注用户的 API
  followUser(userId).then(res => {
    if (!res.success) {
      message.show(res.message)
      return
    }
    message.show('关注成功')
  })
}

// 处理登录需求
const handleLoginRequired = () => {
  console.log('需要登录才能关注用户')
  // TODO: 显示登录弹窗
  // showLoginModal.value = true
}
</script>

<style scoped>
.masonry-container {
  columns: 5;
  column-gap: 16px;
}

.masonry-item {
  break-inside: avoid;
  margin-bottom: 16px;
}

@media (max-width: 1800px) {
  .masonry-container {
    columns: 5;
  }
}

@media (max-width: 1400px) {
  .masonry-container {
    columns: 4;
  }
}

@media (max-width: 1100px) {
  .masonry-container {
    columns: 3;
  }
}

.empty-text {
  font-size: 14px;
  line-height: 18px;
  text-align: center;
  color: var(--color-tertiary-label);
  margin-top: 16px;
}

/* 底线样式 */
.bottom-line {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px 0 40px;
  color: var(--color-tertiary-label);
  font-size: 14px;
}

.bottom-line .line {
  height: 1px;
  width: 80px;
  background-color: #eee;
}

.bottom-line .text {
  padding: 0 16px;
}
</style> 