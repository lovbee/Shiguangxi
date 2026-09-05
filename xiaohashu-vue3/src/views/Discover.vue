<template>
  <div class="discover-page">
    <!-- 分类导航 -->
    <CategoryNav 
      :active-channel-id="activeChannelId" 
      @channel-change="handleChannelChange"
    />

    <LoadingSpinner ref="loadingRef"/>   

    <!-- 瀑布流容器 - 使用固定列布局 -->
    <div v-if="notes.length > 0" class="masonry-grid">
      <!-- 固定列数的瀑布流，每列独立渲染 -->
      <div v-for="colIndex in columnCount" :key="colIndex" class="masonry-column">
        <div 
          v-for="note in getColumnNotes(colIndex-1)" 
          :key="note.id" 
          class="masonry-item"
        >
          <NoteCard 
            :note="note" 
            @click="onNoteClick"
          />
        </div>
      </div>
    </div>
    <div v-else class="flex flex-col items-center justify-center mt-[72px]">
        <div>
          <svg class="icon w-[26rem]" node-id="1" sillyvg="true" template-height="250" template-width="400" version="1.1" viewBox="0 0 400 250" width="400" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><defs node-id="75"><linearGradient gradientUnits="objectBoundingBox" id="linearGradient1" node-id="77" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f8f8f8" stop-opacity="0.082"/><stop offset="1" stop-color="#7c7c7c" stop-opacity="0.059"/></linearGradient><linearGradient gradientUnits="objectBoundingBox" id="linear-gradient-2" node-id="6" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f0eeef" stop-opacity="0"/><stop offset="1" stop-color="#d5d5d5"/></linearGradient><linearGradient gradientUnits="objectBoundingBox" id="linear-gradient" node-id="3" spreadMethod="pad" x1="0.5" x2="0.5" y1="0" y2="1"><stop offset="0" stop-color="#f8f8f8" stop-opacity="0.082"/><stop offset="1" stop-color="#7c7c7c" stop-opacity="0.059"/></linearGradient></defs><g node-id="179"><g node-id="180"><path d="M 0.00 0.00 L 400.00 0.00 L 400.00 250.00 L 0.00 250.00 Z" fill="none" group-id="1,2" id="矩形_2864" node-id="11" stroke="none" target-height="250" target-width="400" target-x="0" target-y="0"/></g><g node-id="181"><g node-id="182"><path d="M 223.10 171.60 L 84.90 171.60 L 83.20 171.40 L 81.80 170.80 L 79.70 168.60 L 79.10 167.20 L 78.90 165.60 L 78.90 100.00 L 79.10 98.40 L 79.70 97.00 L 81.80 94.80 L 83.20 94.20 L 84.90 94.00 L 223.10 94.00 L 224.80 94.20 L 226.20 94.80 L 228.30 97.00 L 228.90 98.40 L 229.10 100.00 L 229.10 165.60 L 228.90 167.20 L 228.30 168.60 L 227.40 169.90 L 226.20 170.80 L 224.80 171.40 L 223.10 171.60 Z" fill="#ffffff" fill-opacity="0.89" fill-rule="nonzero" group-id="1,3,4" node-id="105" stroke="none" target-height="77.600006" target-width="150.20001" target-x="78.9" target-y="94"/><path d="M 223.10 170.60 L 84.90 170.60 L 82.30 169.90 L 80.50 168.10 L 79.90 165.60 L 79.90 100.00 L 80.50 97.50 L 82.30 95.70 L 83.50 95.20 L 223.10 95.00 L 225.70 95.70 L 227.50 97.50 L 228.10 100.00 L 228.10 165.60 L 227.90 167.00 L 226.70 169.10 L 224.50 170.40 L 223.10 170.60 Z" fill="none" group-id="1,3,4" node-id="107" stroke="#c6c7c6" stroke-dasharray="4 4" stroke-linecap="butt" stroke-opacity="0.89" stroke-width="2" target-height="75.600006" target-width="148.20001" target-x="79.9" target-y="95"/></g><g node-id="183"><g node-id="224"><path d="M 194.40 91.00 L 206.40 91.00 L 217.50 91.50 L 227.90 92.50 L 237.40 94.00 L 247.10 96.00 L 256.10 98.40 L 264.30 101.00 L 272.00 104.00 L 279.60 107.50 L 286.60 111.20 L 293.10 115.10 L 299.00 119.10 L 310.20 128.10 L 319.40 137.40 L 325.00 144.00 L 329.80 150.50 L 333.90 156.90 L 340.90 169.80 L 343.60 175.60 L 346.90 184.40 L 349.10 191.70 L 350.70 198.50 L 351.40 203.10 L 351.60 207.00 L 351.40 208.00 L 48.40 208.00 L 49.20 200.00 L 52.00 186.80 L 56.60 172.80 L 62.30 160.40 L 65.80 154.20 L 70.00 147.80 L 74.80 141.30 L 83.10 132.00 L 93.20 122.90 L 98.60 118.80 L 104.70 114.80 L 111.30 110.90 L 118.50 107.20 L 125.70 104.00 L 133.70 101.00 L 142.40 98.40 L 151.80 96.00 L 161.20 94.10 L 171.30 92.60 L 182.40 91.60 L 194.40 91.00 Z" fill="url(#linearGradient1)" fill-rule="nonzero" group-id="1,3,5,46" id="路径_8418" node-id="17" stroke="none" target-height="117" target-width="303.2" target-x="48.4" target-y="91"/></g><g node-id="225"><path d="M 392.50 207.70 L 392.20 208.80 L 391.20 210.10 L 389.20 211.50 L 385.60 213.10 L 381.00 214.60 L 374.70 216.20 L 366.20 217.90 L 353.00 220.00 L 336.10 222.10 L 318.10 223.70 L 297.20 225.20 L 275.30 226.40 L 226.40 227.80 L 200.00 228.00 L 173.60 227.80 L 124.70 226.40 L 102.80 225.20 L 81.90 223.70 L 63.90 222.10 L 47.00 220.00 L 33.80 217.90 L 25.30 216.20 L 14.40 213.10 L 10.80 211.50 L 8.80 210.10 L 7.80 208.80 L 7.50 207.70 L 7.80 206.50 L 8.80 205.30 L 10.80 203.90 L 14.40 202.30 L 19.00 200.70 L 33.80 197.40 L 47.00 195.30 L 63.90 193.30 L 81.90 191.60 L 102.80 190.10 L 124.70 188.90 L 173.60 187.50 L 200.00 187.30 L 226.40 187.50 L 275.30 188.90 L 297.20 190.10 L 318.10 191.60 L 336.10 193.30 L 353.00 195.30 L 366.20 197.40 L 374.70 199.10 L 381.00 200.70 L 385.60 202.30 L 389.20 203.90 L 391.20 205.30 L 392.20 206.50 L 392.50 207.70 Z" fill="url(#linear-gradient-2)" fill-opacity="0.6" fill-rule="nonzero" group-id="1,3,5,47" id="椭圆_622" node-id="18" stroke="none" target-height="40.699997" target-width="385" target-x="7.5" target-y="187.3"/></g><g node-id="226"><g node-id="230"><path d="M 194.40 43.90 L 211.30 44.10 L 226.50 45.80 L 233.50 47.20 L 242.30 49.40 L 250.60 52.10 L 258.40 55.20 L 265.70 58.70 L 272.80 62.60 L 279.50 66.90 L 285.80 71.50 L 291.70 76.40 L 302.50 87.00 L 312.00 98.40 L 317.70 106.40 L 322.80 114.40 L 327.30 122.60 L 335.20 139.10 L 338.30 147.10 L 343.60 162.80 L 348.10 180.30 L 350.90 196.90 L 351.50 202.30 L 351.40 208.00 L 48.40 208.00 L 49.90 191.40 L 53.00 173.50 L 55.40 163.20 L 58.70 151.70 L 61.30 144.00 L 67.90 127.80 L 71.90 119.80 L 76.40 111.80 L 81.40 103.80 L 85.50 98.00 L 94.80 86.90 L 100.00 81.50 L 105.50 76.50 L 111.30 71.70 L 117.70 67.10 L 124.50 62.80 L 131.40 59.00 L 138.90 55.60 L 147.00 52.40 L 155.70 49.70 L 164.30 47.50 L 173.60 45.80 L 183.60 44.60 L 194.40 43.90 Z" fill="url(#linear-gradient)" fill-rule="nonzero" group-id="1,3,5,48,52" id="路径_8419" node-id="20" stroke="none" target-height="164.1" target-width="303.1" target-x="48.4" target-y="43.9"/></g></g><g node-id="227"><path d="M 333.50 152.00 L 285.50 152.00 L 280.90 151.40 L 276.80 149.70 L 273.10 146.90 L 270.30 143.20 L 268.60 139.10 L 268.00 134.50 L 268.20 131.60 L 268.90 128.90 L 270.00 126.40 L 271.50 124.00 L 273.40 121.90 L 275.50 120.20 L 277.90 118.80 L 280.90 117.60 L 282.80 114.60 L 285.00 112.30 L 287.50 110.50 L 290.30 109.10 L 293.30 108.30 L 296.50 108.00 L 299.20 108.20 L 302.60 109.10 L 304.70 105.70 L 306.80 103.50 L 309.30 101.60 L 312.20 100.20 L 315.30 99.30 L 318.50 99.00 L 320.80 99.20 L 325.20 100.30 L 329.10 102.60 L 330.80 104.10 L 332.40 105.80 L 334.60 109.70 L 335.80 114.00 L 336.00 117.20 L 339.50 118.10 L 341.90 119.20 L 344.10 120.60 L 347.80 124.40 L 350.20 129.10 L 350.80 131.70 L 350.80 136.80 L 349.70 141.20 L 347.40 145.10 L 345.90 146.90 L 342.20 149.70 L 338.10 151.40 L 333.50 152.00 Z" fill="#ececec" fill-rule="nonzero" group-id="1,3,5,49" node-id="126" stroke="none" target-height="53" target-width="82.79999" target-x="268" target-y="99"/><path d="M 333.50 151.00 L 336.80 150.70 L 339.80 149.80 L 342.60 148.30 L 345.20 146.20 L 347.20 143.70 L 348.80 140.80 L 349.70 137.80 L 350.00 134.50 L 349.20 129.40 L 347.00 125.00 L 343.50 121.40 L 339.20 119.00 L 335.00 118.00 L 334.70 113.10 L 333.70 110.10 L 332.20 107.30 L 330.10 104.80 L 327.60 102.70 L 324.80 101.20 L 321.70 100.30 L 318.50 100.00 L 315.50 100.30 L 312.60 101.10 L 309.90 102.40 L 307.50 104.20 L 305.50 106.30 L 303.10 110.30 L 299.10 109.20 L 296.50 109.00 L 293.50 109.30 L 290.70 110.10 L 288.00 111.40 L 285.60 113.10 L 283.60 115.20 L 281.60 118.50 L 278.30 119.70 L 276.10 121.00 L 274.00 122.60 L 272.30 124.60 L 270.90 126.90 L 269.80 129.30 L 269.20 131.80 L 269.00 134.50 L 269.30 137.80 L 270.20 140.80 L 271.80 143.70 L 273.80 146.20 L 276.40 148.30 L 279.20 149.80 L 282.20 150.70 L 285.50 151.00 L 333.50 151.00 M 333.50 153.00 L 285.50 153.00 L 282.10 152.70 L 279.00 151.90 L 276.20 150.50 L 273.60 148.60 L 271.40 146.40 L 269.50 143.80 L 268.20 141.00 L 267.30 137.90 L 267.00 134.50 L 267.80 129.10 L 270.00 124.40 L 273.40 120.50 L 277.70 117.70 L 280.20 116.80 L 282.00 114.00 L 284.20 111.70 L 286.90 109.70 L 289.80 108.30 L 293.00 107.40 L 296.50 107.00 L 299.40 107.20 L 302.10 107.90 L 303.90 105.10 L 306.20 102.70 L 308.80 100.70 L 311.80 99.30 L 315.00 98.40 L 318.50 98.00 L 321.90 98.30 L 324.90 99.20 L 327.80 100.50 L 330.40 102.30 L 332.60 104.50 L 334.40 107.10 L 335.80 109.90 L 336.70 113.00 L 337.00 116.30 L 339.80 117.10 L 342.30 118.30 L 344.70 119.80 L 346.80 121.60 L 348.50 123.70 L 350.00 126.20 L 351.10 128.80 L 351.80 131.50 L 352.00 134.50 L 351.70 137.90 L 350.80 141.00 L 349.50 143.80 L 347.60 146.40 L 345.40 148.60 L 342.80 150.50 L 340.00 151.90 L 336.90 152.70 L 333.50 153.00 Z" fill="#c6c7c6" fill-rule="nonzero" group-id="1,3,5,49" node-id="128" stroke="none" target-height="55" target-width="85" target-x="267" target-y="98"/></g><g node-id="228"><path d="M 146.40 213.80 L 146.10 210.30 L 146.20 207.90 L 146.70 205.50 L 147.70 203.00 L 149.30 200.70 L 151.00 199.00 L 152.90 197.50 L 156.30 195.80 L 156.70 199.60 L 156.50 201.90 L 156.00 204.40 L 155.00 206.90 L 153.50 209.10 L 151.70 210.90 L 149.80 212.30 L 146.40 214.10 Z M 155.90 196.40 L 153.90 197.50 L 150.90 199.70 L 148.10 203.20 L 146.80 207.40 L 146.60 211.10 L 146.80 213.40 L 148.80 212.40 L 151.80 210.10 L 154.60 206.70 L 156.00 202.40 L 156.20 198.70 L 155.90 196.40 Z" fill="#f1f1f1" fill-rule="nonzero" group-id="1,3,5,50" id="路径_8429" node-id="24" stroke="none" target-height="18.300003" target-width="10.599991" target-x="146.1" target-y="195.8"/></g><path d="M 153.00 205.20 L 150.80 206.80 L 149.20 208.60 L 147.90 210.60 L 146.40 213.70 L 149.90 213.90 L 154.60 213.00 L 157.00 211.90 L 159.20 210.20 L 162.20 206.50 L 163.60 203.40 L 160.20 203.20 L 157.90 203.40 L 155.50 204.00 L 153.00 205.20 Z" fill="#f1f1f1" fill-rule="nonzero" group-id="1,3,5,51" id="路径_8430" node-id="25" stroke="none" target-height="10.699997" target-width="17.200012" target-x="146.4" target-y="203.2"/></g><g node-id="184"><path d="M 140.00 107.00 L 262.00 107.00 L 263.80 107.20 L 267.00 108.30 L 268.50 109.30 L 270.60 111.90 L 271.80 115.20 L 272.00 160.00 L 271.40 163.50 L 269.60 166.40 L 267.00 168.60 L 263.80 169.80 L 140.00 170.00 L 138.20 169.80 L 135.00 168.60 L 133.50 167.60 L 131.40 165.00 L 130.20 161.80 L 130.00 117.00 L 130.60 113.50 L 132.40 110.50 L 135.00 108.30 L 136.50 107.60 L 140.00 107.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,6" node-id="141" stroke="none" target-height="63" target-width="142" target-x="130" target-y="107"/><path d="M 140.00 108.00 L 262.00 108.00 L 264.40 108.30 L 266.50 109.20 L 268.40 110.60 L 269.80 112.40 L 270.70 114.60 L 271.00 117.00 L 271.00 160.00 L 270.70 162.40 L 269.80 164.50 L 268.40 166.30 L 266.50 167.80 L 264.40 168.70 L 262.00 169.00 L 140.00 169.00 L 137.60 168.70 L 135.50 167.80 L 133.60 166.30 L 132.20 164.50 L 131.30 162.40 L 131.00 160.00 L 131.00 117.00 L 131.30 114.60 L 132.20 112.40 L 133.60 110.60 L 135.50 109.20 L 137.60 108.30 L 140.00 108.00 Z" fill="none" group-id="1,3,6" node-id="143" stroke="#c6c7c6" stroke-linecap="butt" stroke-width="2" target-height="61" target-width="140" target-x="131" target-y="108"/></g><g node-id="185"><path d="M 160.00 51.00 L 204.00 51.00 L 207.50 51.60 L 209.00 52.30 L 211.60 54.50 L 213.40 57.50 L 214.00 61.00 L 213.80 87.80 L 212.60 91.00 L 210.50 93.60 L 207.50 95.40 L 204.00 96.00 L 160.00 96.00 L 156.50 95.40 L 155.00 94.60 L 152.40 92.40 L 150.60 89.50 L 150.00 86.00 L 150.20 59.20 L 151.40 55.90 L 153.50 53.30 L 156.50 51.60 L 160.00 51.00 Z" fill="#ffffff" fill-rule="nonzero" group-id="1,3,7" node-id="147" stroke="none" target-height="45" target-width="64" target-x="150" target-y="51"/><path d="M 160.00 52.00 L 204.00 52.00 L 206.40 52.30 L 208.50 53.20 L 210.40 54.60 L 211.80 56.40 L 212.70 58.60 L 213.00 61.00 L 213.00 86.00 L 212.70 88.40 L 211.80 90.50 L 210.40 92.30 L 208.50 93.80 L 206.40 94.70 L 204.00 95.00 L 160.00 95.00 L 157.60 94.70 L 155.50 93.80 L 153.60 92.30 L 152.20 90.50 L 151.30 88.40 L 151.00 86.00 L 151.00 61.00 L 151.30 58.60 L 152.20 56.40 L 153.60 54.60 L 155.50 53.20 L 157.60 52.30 L 160.00 52.00 Z" fill="none" group-id="1,3,7" node-id="149" stroke="#c6c7c6" stroke-linecap="butt" stroke-width="2" target-height="43" target-width="62" target-x="151" target-y="52"/></g><g node-id="186"><path d="M 161.00 60.00 L 176.00 60.00 L 178.50 60.70 L 180.30 62.50 L 181.00 65.00 L 181.00 80.00 L 180.30 82.50 L 178.50 84.30 L 177.40 84.80 L 161.00 85.00 L 158.50 84.30 L 156.70 82.50 L 156.00 80.00 L 156.20 63.60 L 156.70 62.50 L 158.50 60.70 L 161.00 60.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,8" id="矩形_2827" node-id="32" stroke="none" target-height="25" target-width="25" target-x="156" target-y="60"/></g><g node-id="187"><path d="M 186.00 62.00 L 207.00 62.00 L 207.80 62.10 L 208.80 63.20 L 208.80 64.80 L 207.80 65.80 L 186.00 66.00 L 184.60 65.40 L 184.00 64.00 L 184.60 62.60 L 186.00 62.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,9" id="矩形_2826" node-id="33" stroke="none" target-height="4" target-width="24.800003" target-x="184" target-y="62"/></g><g node-id="188"><path d="M 186.00 69.00 L 207.00 69.00 L 207.80 69.10 L 208.80 70.20 L 208.80 71.80 L 207.80 72.80 L 186.00 73.00 L 184.60 72.40 L 184.00 71.00 L 184.60 69.60 L 186.00 69.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,10" id="矩形_2825" node-id="34" stroke="none" target-height="4" target-width="24.800003" target-x="184" target-y="69"/></g><g node-id="189"><path d="M 186.00 81.00 L 195.80 81.10 L 196.80 82.20 L 197.00 83.00 L 196.80 83.80 L 195.80 84.80 L 185.20 84.80 L 184.20 83.80 L 184.20 82.20 L 185.20 81.10 L 186.00 81.00 Z" fill="#fce6d8" fill-rule="nonzero" group-id="1,3,11" id="矩形_2824" node-id="35" stroke="none" target-height="3.800003" target-width="12.800003" target-x="184.2" target-y="81"/></g><g node-id="190"><path d="M 277.00 205.00 L 123.00 205.00 L 121.40 204.80 L 119.70 204.10 L 117.80 202.90 L 115.60 200.80 L 113.20 197.90 L 109.00 190.60 L 92.00 131.30 L 92.40 129.10 L 93.00 128.80 L 101.10 131.70 L 106.00 132.50 L 234.40 132.50 L 235.80 132.20 L 239.00 130.80 L 252.10 122.90 L 283.80 122.90 L 295.60 122.50 L 302.80 122.90 L 304.90 123.50 L 306.50 124.40 L 308.30 126.60 L 308.90 129.10 L 309.00 131.30 L 291.10 190.60 L 288.60 195.30 L 284.10 201.20 L 280.80 203.90 L 278.90 204.70 L 277.00 205.00 Z" fill="#ffffff" fill-rule="nonzero" group-id="1,3,12" node-id="169" stroke="none" target-height="82.5" target-width="217" target-x="92" target-y="122.5"/><path d="M 295.60 123.50 L 283.90 123.90 L 252.40 123.90 L 239.40 131.70 L 236.10 133.10 L 234.40 133.50 L 106.00 133.50 L 100.80 132.60 L 93.20 129.80 L 93.00 131.20 L 109.90 190.30 L 112.40 194.90 L 116.30 200.10 L 120.10 203.20 L 123.00 204.00 L 277.00 204.00 L 279.90 203.20 L 283.70 200.20 L 286.00 197.40 L 290.20 190.30 L 308.00 131.20 L 308.00 129.30 L 307.40 127.10 L 305.70 125.10 L 302.60 123.90 L 295.60 123.50 M 295.60 121.50 L 302.90 121.90 L 304.80 122.40 L 307.30 123.80 L 308.60 125.10 L 309.30 126.60 L 309.80 128.10 L 310.00 131.50 L 292.00 191.00 L 287.70 198.50 L 283.90 202.80 L 280.20 205.30 L 277.00 206.00 L 123.00 206.00 L 119.80 205.30 L 116.20 202.80 L 114.20 200.70 L 110.90 196.30 L 108.00 191.00 L 91.00 131.50 L 91.20 129.60 L 91.50 128.60 L 92.20 128.00 L 93.00 127.80 L 94.40 128.00 L 100.80 130.50 L 103.30 131.20 L 106.00 131.50 L 234.40 131.50 L 237.40 130.50 L 241.80 128.10 L 251.80 121.90 L 283.80 121.90 L 295.60 121.50 Z" fill="#c6c7c6" fill-rule="nonzero" group-id="1,3,12" node-id="171" stroke="none" target-height="84.5" target-width="219" target-x="91" target-y="121.5"/></g><g node-id="191"><path d="M 116.00 69.00 L 160.00 69.00 L 163.50 69.60 L 166.50 71.30 L 168.60 73.90 L 169.80 77.20 L 169.80 105.80 L 169.40 107.50 L 167.60 110.40 L 165.00 112.60 L 161.80 113.80 L 116.00 114.00 L 112.50 113.40 L 109.50 111.60 L 107.40 109.00 L 106.20 105.80 L 106.20 77.20 L 107.40 73.90 L 109.50 71.30 L 112.50 69.60 L 116.00 69.00 Z" fill="#ffffff" fill-rule="nonzero" group-id="1,3,13" node-id="175" stroke="none" target-height="45" target-width="63.600006" target-x="106.2" target-y="69"/><path d="M 116.00 70.00 L 160.00 70.00 L 162.40 70.30 L 164.50 71.20 L 166.40 72.60 L 167.80 74.40 L 168.70 76.60 L 169.00 79.00 L 169.00 104.00 L 168.70 106.40 L 167.80 108.50 L 166.40 110.30 L 164.50 111.80 L 162.40 112.70 L 160.00 113.00 L 116.00 113.00 L 113.60 112.70 L 111.50 111.80 L 109.60 110.30 L 108.20 108.50 L 107.30 106.40 L 107.00 104.00 L 107.00 79.00 L 107.30 76.60 L 108.20 74.40 L 109.60 72.60 L 111.50 71.20 L 113.60 70.30 L 116.00 70.00 Z" fill="none" group-id="1,3,13" node-id="177" stroke="#c6c7c6" stroke-linecap="butt" stroke-width="2" target-height="43" target-width="62" target-x="107" target-y="70"/></g><g node-id="192"><path d="M 118.00 78.00 L 133.00 78.00 L 135.50 78.70 L 137.30 80.50 L 138.00 83.00 L 138.00 98.00 L 137.30 100.50 L 135.50 102.30 L 134.40 102.80 L 118.00 103.00 L 115.50 102.30 L 113.70 100.50 L 113.00 98.00 L 113.20 81.60 L 113.70 80.50 L 115.50 78.70 L 118.00 78.00 Z" fill="#fce6d8" fill-rule="nonzero" group-id="1,3,14" id="矩形_2820" node-id="42" stroke="none" target-height="25" target-width="25" target-x="113" target-y="78"/></g><g node-id="193"><path d="M 143.00 80.00 L 164.00 80.00 L 164.80 80.10 L 165.80 81.20 L 165.80 82.80 L 164.80 83.80 L 143.00 84.00 L 141.60 83.40 L 141.00 82.00 L 141.60 80.60 L 143.00 80.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,15" id="矩形_2821" node-id="43" stroke="none" target-height="4" target-width="24.800003" target-x="141" target-y="80"/></g><g node-id="194"><path d="M 143.00 87.00 L 164.00 87.00 L 164.80 87.10 L 165.80 88.20 L 165.80 89.80 L 164.80 90.80 L 143.00 91.00 L 141.60 90.40 L 141.00 89.00 L 141.60 87.60 L 143.00 87.00 Z" fill="#eeeeee" fill-rule="nonzero" group-id="1,3,16" id="矩形_2822" node-id="44" stroke="none" target-height="4" target-width="24.800003" target-x="141" target-y="87"/></g><g node-id="195"><path d="M 143.00 99.00 L 152.80 99.10 L 153.80 100.20 L 153.80 101.80 L 152.80 102.80 L 152.00 103.00 L 142.20 102.80 L 141.20 101.80 L 141.20 100.20 L 142.20 99.10 L 143.00 99.00 Z" fill="#fce6d8" fill-rule="nonzero" group-id="1,3,17" id="矩形_2823" node-id="45" stroke="none" target-height="4" target-width="12.600006" target-x="141.2" target-y="99"/></g><g node-id="196"><path d="M 186.50 31.50 L 186.50 50.50" fill="none" group-id="1,3,18" id="直线_2051" node-id="46" stroke="#c6c7c6" stroke-dasharray="5 5" stroke-linecap="round" stroke-width="1" target-height="19" target-width="0" target-x="186.5" target-y="31.5"/></g><g node-id="197"><path d="M 175.50 22.00 L 175.50 41.00" fill="none" group-id="1,3,19" id="直线_2052" node-id="47" stroke="#c6c7c6" stroke-dasharray="5 5" stroke-linecap="round" stroke-width="1" target-height="19" target-width="0" target-x="175.5" target-y="22"/></g><g node-id="198"><path d="M 143.50 48.00 L 143.50 67.00" fill="none" group-id="1,3,20" id="直线_2053" node-id="48" stroke="#c6c7c6" stroke-dasharray="5 5" stroke-linecap="round" stroke-width="1" target-height="19" target-width="0" target-x="143.5" target-y="48"/></g><g node-id="199"><path d="M 128.50 52.50 L 128.50 64.00" fill="none" group-id="1,3,21" id="直线_2054" node-id="49" stroke="#c6c7c6" stroke-dasharray="5 5" stroke-linecap="round" stroke-width="1" target-height="11.5" target-width="0" target-x="128.5" target-y="52.5"/></g><g node-id="200"><path d="M 265.40 65.90 L 266.30 65.20 L 267.30 65.90 L 269.90 73.90 L 277.90 76.50 L 278.60 77.50 L 277.90 78.40 L 269.90 81.00 L 267.30 89.10 L 266.30 89.80 L 265.40 89.10 L 262.80 81.00 L 254.70 78.40 L 254.00 77.50 L 254.70 76.50 L 262.40 74.20 L 263.00 73.50 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,22" id="多边形_21" node-id="50" stroke="none" target-height="24.600006" target-width="24.600006" target-x="254" target-y="65.2"/></g><g node-id="201"><path d="M 240.20 31.80 L 241.70 36.80 L 246.70 38.30 L 241.70 39.90 L 240.20 44.80 L 238.70 39.90 L 233.70 38.30 L 238.70 36.80 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,23" id="多边形_22" node-id="51" stroke="none" target-height="13" target-width="13" target-x="233.7" target-y="31.8"/></g><g node-id="202"><path d="M 271.20 38.30 L 272.70 43.30 L 277.70 44.80 L 272.70 46.40 L 271.20 51.40 L 269.70 46.40 L 264.70 44.80 L 269.70 43.30 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,24" id="多边形_23" node-id="52" stroke="none" target-height="13.100002" target-width="13" target-x="264.7" target-y="38.3"/></g><g node-id="203"><path d="M 166.20 181.90 L 166.40 183.40 L 167.00 184.30 L 167.80 184.80 L 168.90 185.10 L 191.60 185.10 L 192.60 184.80 L 194.00 183.40 L 194.10 181.00 L 193.20 179.80 L 181.40 179.80 L 180.90 179.30 L 168.90 179.30 L 167.80 179.50 L 167.00 180.10 L 166.40 180.90 L 166.20 181.90 Z" fill="#cccccc" fill-rule="nonzero" group-id="1,3,25" id="路径_8560" node-id="53" stroke="none" target-height="5.800003" target-width="27.90001" target-x="166.2" target-y="179.3"/></g><g node-id="204"><path d="M 181.50 204.60 L 178.70 204.60 L 178.70 184.90 L 181.50 184.90 Z" fill="#cccccc" fill-rule="nonzero" group-id="1,3,26" id="矩形_2831" node-id="54" stroke="none" target-height="19.700012" target-width="2.800003" target-x="178.7" target-y="184.9"/></g><g node-id="205"><path d="M 170.80 204.50 L 189.70 204.50 L 188.40 203.70 L 185.00 202.50 L 180.20 201.90 L 175.50 202.50 L 172.10 203.70 L 170.80 204.50 Z" fill="#cccccc" fill-rule="nonzero" group-id="1,3,27" id="路径_8561" node-id="55" stroke="none" target-height="2.600006" target-width="18.899994" target-x="170.8" target-y="201.9"/></g><g node-id="206"><path d="M 194.40 202.10 L 197.10 202.10 L 198.30 191.90 L 194.40 191.90 Z" fill="#a0616a" fill-rule="nonzero" group-id="1,3,28" id="路径_8562" node-id="56" stroke="none" target-height="10.200012" target-width="3.9000092" target-x="194.4" target-y="191.9"/></g><g node-id="207"><path d="M 193.70 201.30 L 199.00 201.30 L 200.30 201.50 L 201.30 202.20 L 202.00 203.30 L 202.30 204.60 L 193.70 204.70 Z" fill="#2f2e41" fill-rule="nonzero" group-id="1,3,29" id="路径_8563" node-id="57" stroke="none" target-height="3.399994" target-width="8.600006" target-x="193.7" target-y="201.3"/></g><g node-id="208"><path d="M 184.10 196.70 L 182.00 198.20 L 174.90 190.70 L 178.10 188.40 Z" fill="#a0616a" fill-rule="nonzero" group-id="1,3,30" id="路径_8564" node-id="58" stroke="none" target-height="9.800003" target-width="9.200012" target-x="174.9" target-y="188.4"/></g><g node-id="209"><path d="M 186.20 198.40 L 179.20 203.30 L 178.60 202.10 L 178.60 200.80 L 179.00 199.60 L 179.90 198.70 L 184.20 195.60 Z" fill="#2f2e41" fill-rule="nonzero" group-id="1,3,31" id="路径_8565" node-id="59" stroke="none" target-height="7.699997" target-width="7.599991" target-x="178.6" target-y="195.6"/></g><g node-id="210"><path d="M 187.00 156.80 L 185.60 156.10 L 184.10 155.90 L 182.60 156.10 L 181.20 156.80 L 179.10 174.20 L 185.40 174.20 L 186.30 168.70 L 188.40 160.30 Z" fill="#cccccc" fill-rule="nonzero" group-id="1,3,32" id="路径_8566" node-id="60" stroke="none" target-height="18.300003" target-width="9.299988" target-x="179.1" target-y="155.9"/></g><g node-id="211"><path d="M 193.30 183.70 L 182.10 180.00 L 176.70 184.30 L 182.40 193.00 L 179.40 196.90 L 174.70 191.10 L 171.60 186.80 L 170.30 183.70 L 171.30 178.00 L 174.10 174.00 L 178.10 172.90 L 191.40 174.70 L 196.70 178.00 L 197.70 178.80 L 198.60 181.10 L 199.30 200.00 L 193.50 200.00 Z" fill="#2f2e41" fill-rule="nonzero" group-id="1,3,33" id="路径_8567" node-id="61" stroke="none" target-height="27.100006" target-width="29" target-x="170.3" target-y="172.9"/></g><g node-id="212"><path d="M 186.20 179.60 L 184.10 178.00 L 181.30 174.70 L 174.90 177.50 L 173.00 177.50 L 172.00 178.20 L 171.40 179.50 L 170.40 177.10 L 170.30 175.80 L 171.10 174.00 L 173.60 171.80 L 175.90 168.50 L 174.30 159.90 L 177.60 157.50 L 179.10 156.90 L 182.30 156.20 L 182.40 171.70 L 183.30 170.00 L 184.30 166.20 L 186.10 156.30 L 190.40 157.70 L 192.00 158.90 L 188.90 167.40 L 187.90 168.80 L 187.90 170.60 L 193.30 175.30 L 189.40 178.60 L 188.00 179.40 L 186.20 179.60 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,34" id="路径_8568" node-id="62" stroke="none" target-height="23.40001" target-width="23" target-x="170.3" target-y="156.2"/></g><g node-id="213"><path d="M 186.60 144.70 L 187.70 145.50 L 189.10 147.80 L 189.20 150.40 L 188.70 151.70 L 186.80 153.70 L 184.30 154.40 L 183.00 154.30 L 181.60 153.80 L 179.70 151.90 L 178.90 149.40 L 179.60 146.80 L 180.40 145.60 L 182.70 144.30 L 185.30 144.20 L 186.60 144.70 Z" fill="#ffb9b9" fill-rule="nonzero" group-id="1,3,35" id="椭圆_685" node-id="63" stroke="none" target-height="10.199997" target-width="10.300003" target-x="178.9" target-y="144.2"/></g><g node-id="214"><path d="M 182.80 181.10 L 183.70 179.60 L 185.40 179.40 L 188.40 175.90 L 191.00 177.10 L 185.80 183.20 L 184.30 183.40 L 183.60 183.00 L 182.80 181.90 L 182.80 181.10 Z" fill="#a0616a" fill-rule="nonzero" group-id="1,3,36" id="路径_8569" node-id="64" stroke="none" target-height="7.5" target-width="8.199997" target-x="182.8" target-y="175.9"/></g><g node-id="215"><path d="M 184.90 178.10 L 189.60 171.80 L 188.40 165.50 L 190.30 158.50 L 191.10 158.30 L 192.30 158.60 L 193.00 161.50 L 193.50 166.00 L 194.20 172.50 L 194.00 174.20 L 193.50 175.80 L 188.50 181.70 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,37" id="路径_8570" node-id="65" stroke="none" target-height="23.399994" target-width="9.300003" target-x="184.9" target-y="158.3"/></g><g node-id="216"><path d="M 188.60 147.90 L 187.60 148.80 L 185.30 149.50 L 181.50 148.90 L 181.00 152.30 L 180.20 153.80 L 180.10 153.00 L 179.70 152.50 L 178.40 151.90 L 178.30 150.50 L 176.90 148.30 L 177.10 146.80 L 179.50 143.90 L 180.60 143.20 L 181.90 143.20 L 183.70 142.10 L 184.70 142.00 L 186.30 142.30 L 187.70 143.10 L 189.80 145.00 L 188.70 147.80" fill="#2f2e41" fill-rule="nonzero" group-id="1,3,38" id="路径_8571" node-id="66" stroke="none" target-height="11.800003" target-width="12.900009" target-x="176.9" target-y="142"/></g><g node-id="218"><path d="M 187.20 184.00 L 181.30 184.00 L 181.70 180.10 L 181.70 178.30 L 181.30 176.90 L 187.20 176.90 L 187.80 178.60 L 188.00 180.40 L 187.80 182.20 L 187.20 184.00 Z" fill="#40d79e" fill-rule="nonzero" group-id="1,3,40" id="路径_8573" node-id="68" stroke="none" target-height="7.100006" target-width="6.699997" target-x="181.3" target-y="176.9"/></g><g node-id="219"><path d="M 184.60 182.60 L 183.70 181.20 L 182.00 180.90 L 179.00 177.40 L 176.40 178.60 L 181.60 184.70 L 183.10 184.90 L 183.80 184.60 L 184.60 183.40 L 184.60 182.60 Z" fill="#a0616a" fill-rule="nonzero" group-id="1,3,41" id="路径_8574" node-id="69" stroke="none" target-height="7.5" target-width="8.200012" target-x="176.4" target-y="177.4"/></g><g node-id="220"><path d="M 178.80 182.00 L 173.00 177.20 L 171.60 175.70 L 171.20 173.60 L 171.10 169.90 L 173.10 161.10 L 173.70 160.20 L 174.50 159.70 L 175.50 159.40 L 176.60 159.70 L 175.50 171.90 L 181.20 179.50 L 178.90 182.00 Z" fill="#e97c2c" fill-rule="nonzero" group-id="1,3,42" id="路径_8575" node-id="70" stroke="none" target-height="22.600006" target-width="10.099991" target-x="171.1" target-y="159.4"/></g><g node-id="221"><path d="M 233.40 169.30 L 222.50 169.30 L 223.80 162.10 L 223.80 160.00 L 223.40 158.00 L 222.50 156.20 L 233.40 156.20 L 234.30 158.30 L 235.00 162.70 L 234.30 167.20 L 233.40 169.30 Z" fill="#40d79e" fill-rule="nonzero" group-id="1,3,43" id="路径_8555" node-id="71" stroke="none" target-height="13.100006" target-width="12.5" target-x="222.5" target-y="156.2"/></g><g node-id="222"><path d="M 233.70 189.90 L 244.70 189.90 L 244.90 187.40 L 244.40 178.60 L 244.70 176.80 L 233.70 176.80 L 232.90 179.00 L 232.20 183.40 L 232.90 187.80 L 233.70 189.90 Z" fill="#e6e6e6" fill-rule="nonzero" group-id="1,3,44" id="路径_8559" node-id="72" stroke="none" target-height="13.099991" target-width="12.699997" target-x="232.2" target-y="176.8"/></g><path d="M 264.20 130.80 L 291.30 130.80 L 292.00 131.10 L 292.30 131.80 L 292.00 132.50 L 291.30 132.80 L 264.20 132.80 L 263.50 132.50 L 263.20 131.80 L 263.50 131.10 L 264.20 130.80 Z" fill="#c6c7c6" fill-rule="nonzero" group-id="1,3,45" id="矩形_2828" node-id="73" stroke="none" target-height="2" target-width="29.099976" target-x="263.2" target-y="130.8"/></g></g></svg>
        </div>
        <div class="empty-text">该频道下暂无笔记</div>
    </div>

    <!-- 底线提示 -->
    <div v-if="notes.length > 0 && !hasMore" class="bottom-line">
      <div class="line"></div>
      <div class="text">小哈是有底线的</div>
      <div class="line"></div>
    </div>

    <!-- 笔记详情模态框 -->
    <NoteDetailModal 
      v-model:visible="showModal"
      :note="selectedNote"
    />
  </div>
</template>

<script setup>
import NoteCard from '@/components/note/NoteCard.vue'
import NoteDetailModal from '@/components/note/NoteDetailModal.vue'
import CategoryNav from '@/components/layout/CategoryNav.vue'
import { ref, onMounted, watch, onBeforeUnmount, computed } from 'vue'
import { getDiscoverNotePageList } from '@/api/note'
import { useRoute, useRouter } from 'vue-router'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'


const route = useRoute()
const router = useRouter()

// 笔记数据
const notes = ref([])
const currPageNo = ref(1)
const hasMore = ref(true) // 是否有更多数据
const isLoading = ref(false) // 是否正在加载数据


// 瀑布流列数
const columnCount = 5

// 根据屏幕宽度计算列数
const getColumnCount = () => {
  const width = window.innerWidth
  if (width <= 1100) return 3
  if (width <= 1400) return 4
  return 5
}

// 获取指定列的笔记
const getColumnNotes = (colIndex) => {
  return notes.value.filter((_, index) => index % columnCount === colIndex)
}

const loadingRef = ref(null)

// 当前激活的频道ID
const activeChannelId = ref(0) // 默认为0，表示全部

// 模态框状态
const showModal = ref(false)
const selectedNote = ref(null)

// 从URL参数中获取频道ID
const getChannelIdFromRoute = () => {
  const channelId = route.query.channelId
  return channelId ? parseInt(channelId) : 0
}

// 加载笔记数据
const loadNotes = (channelId = 0, isFirstPage = true) => {
  if (isLoading.value) return
  
  isLoading.value = true
  
  // 如果是加载第一页，显示加载指示器并重置页码
  if (isFirstPage) {
    loadingRef.value.show()
    currPageNo.value = 1
    notes.value = []
  }
  
  // 调用API获取笔记列表
  getDiscoverNotePageList(channelId, currPageNo.value).then(res => {
    console.log('加载笔记数据:', res)
    if (res.success) {
      const newNotes = res.data || []
      
      if (isFirstPage) {
        notes.value = newNotes
      } else {
        // 追加数据到现有列表末尾
        notes.value = [...notes.value, ...newNotes]
      }
      
      // 判断是否还有更多数据
      hasMore.value = newNotes.length > 0
      
      // 如果有数据返回，增加页码
      if (newNotes.length > 0) {
        currPageNo.value++
      }
    }
  }).finally(() => {
    isLoading.value = false
    if (isFirstPage) {
      loadingRef.value.hide()
    }
  })
}

// 加载更多数据
const loadMoreNotes = () => {
  if (!hasMore.value || isLoading.value) return
  loadNotes(activeChannelId.value, false)
}

// 处理频道变更
const handleChannelChange = (channelId) => {
  console.log('Discover 组件接收到频道变更:', channelId)
  activeChannelId.value = channelId
  
  // 更新URL参数
  updateRouteQuery(channelId)
  
  // 加载对应频道的笔记（第一页）
  loadNotes(channelId, true)
}

// 更新URL查询参数
const updateRouteQuery = (channelId) => {
  // 如果是默认频道(0)，则移除查询参数
  const query = channelId === 0 ? {} : { channelId }
  
  // 使用replace方法更新URL，不添加新的历史记录
  router.replace({ 
    path: route.path, 
    query 
  })
}

// 点击笔记卡片时的处理函数
const onNoteClick = (note) => {
  console.log('点击了笔记，ID:', note.id)
  selectedNote.value = note
  showModal.value = true
}

// 监听滚动事件，检测是否滚动到底部
const handleScroll = () => {
  const scrollTop = document.documentElement.scrollTop || document.body.scrollTop
  const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight
  const clientHeight = document.documentElement.clientHeight || window.innerHeight
  
  // 当距离底部小于100px时，认为已经滚动到底部
  if (scrollHeight - scrollTop - clientHeight < 100) {
    console.log('已滚动到页面底部，加载更多数据')
    loadMoreNotes()
  }
}

// 组件挂载时添加滚动监听
onMounted(() => {
  // 从URL获取频道ID
  const channelId = getChannelIdFromRoute()
  activeChannelId.value = channelId
  
  // 加载笔记数据
  loadNotes(channelId, true)
  
  // 添加滚动事件监听
  window.addEventListener('scroll', handleScroll)
})

// 组件卸载前移除滚动监听
onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
})

// 监听路由变化
watch(() => route.query.channelId, (newChannelId) => {
  const channelId = newChannelId ? parseInt(newChannelId) : 0
  if (activeChannelId.value !== channelId) {
    activeChannelId.value = channelId
    loadNotes(channelId, true)
  }
}, { immediate: true })
</script>

<style scoped>
/* 使用固定列布局的瀑布流 */
.masonry-grid {
  display: flex;
  width: 100%;
  padding: 0 1px;
  position: relative;
  z-index: 1;
}

.masonry-column {
  flex: 1;
  padding: 0 8px;
}

.masonry-item {
  margin-bottom: 16px;
}

/* 响应式布局 */
@media (max-width: 1100px) {
  .masonry-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  
  .masonry-column {
    padding: 0;
  }
}

@media (min-width: 1101px) and (max-width: 1400px) {
  .masonry-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
  }
  
  .masonry-column {
    padding: 0;
  }
}

@media (min-width: 1401px) {
  .masonry-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
  }
  
  .masonry-column {
    padding: 0;
  }
}

/* 动画效果 */
.masonry-grid {
  opacity: 0;
  animation: fadeIn 0.3s ease-in-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.discover-page {
  min-height: 100vh;
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