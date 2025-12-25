<template>
  <div class="h-[calc(100vh-80px)] w-full overflow-hidden bg-black relative">
    <!-- Video Background -->
    <div class="absolute inset-0 w-full h-full">
      <video 
        autoplay 
        muted 
        loop 
        playsinline 
        class="w-full h-full object-cover"
      >
        <source src="@/assets/landingbg.mp4" type="video/mp4" />
        <div class="absolute inset-0 bg-gray-900" />
      </video>
      <!-- Overlay -->
      <div class="absolute inset-0 bg-black/60 z-10"></div>
    </div>

    <!-- Content Overlay -->
    <div class="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full h-full flex items-center">
      <div class="grid md:grid-cols-2 gap-12 items-center w-full">
        <!-- Left Text -->
        <div class="text-white">
          <div class="inline-flex items-center px-3 py-1 bg-white/10 backdrop-blur-sm border border-white/20 text-white rounded-full text-sm mb-6">
            <span class="w-2 h-2 rounded-full bg-green-400 mr-2 animate-pulse" />
            알바생을 위한 근로 관리 필수 앱
          </div>
          
          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 tracking-tight leading-tight text-shadow-lg">
            <span class="block">내 알바 급여와 권리,</span>
            <span class="block text-brand-300">한 번에 관리하세요</span>
          </h1>
          
          <p class="text-lg text-gray-200 mb-8 leading-relaxed max-w-lg">
            일한 시간만 입력하면 <span class="font-semibold text-white">급여와 수당을 자동 계산</span>하고,<br class="hidden sm:block" />
            궁금한 건 AI에게 물어보고, 서류와 이력까지 깔끔하게 정리해요.
          </p>
          
          <div class="flex flex-col sm:flex-row gap-4 mb-10">
            <button 
              class="w-full max-w-lg px-8 py-4 text-lg font-bold bg-brand-600 text-white rounded-xl hover:bg-brand-500 transition-all transform hover:scale-105 shadow-lg shadow-brand-900/50 flex items-center justify-center"
              @click="router.push('/dashboard')"
            >
              내 알바 관리 시작하기
              <svg class="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
            </button>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-3 gap-6 text-sm text-gray-300 border-t border-white/10 pt-6">
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
              <span>급여·수당 자동 계산</span>
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
              <span>AI 근로 상담</span>
            </div>
            <div class="flex items-center gap-2">
              <svg class="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <span>근로서류 & 이력서</span>
            </div>
          </div>
        </div>
        
        <!-- Right Card (Floating) -->
        <div class="relative hidden md:block">
           <div class="absolute -top-10 -right-10 w-64 h-64 bg-brand-500 rounded-full blur-[100px] opacity-30 mix-blend-screen animate-pulse" />
          
           <!-- Stacked Cards Container -->
           <div class="relative space-y-4">
             
             <!-- Card 1: Pay Summary -->
             <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl p-5 border border-white/50 transform translate-x-4 hover:translate-x-0 transition-transform duration-500">
               <div class="flex justify-between items-center mb-3">
                 <div class="flex items-center gap-3">
                   <div class="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center text-xl">💰</div>
                   <div>
                     <p class="text-xs text-brand-600 font-bold">12월 급여 요약</p>
                     <p class="text-sm font-bold text-gray-900">스타벅스 강남점</p>
                   </div>
                 </div>
                 <span class="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded-lg">주휴수당 O</span>
               </div>
               <div class="flex justify-between items-end border-t border-gray-100 pt-3">
                 <span class="text-xs text-gray-500">예상 입금액</span>
                 <span class="text-lg font-bold text-gray-900">1,280,300원</span>
               </div>
             </div>

             <!-- Card 2: AI Tech -->
             <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl p-5 border border-white/50 -translate-x-2 hover:translate-x-0 transition-transform duration-500 z-10">
               <div class="flex items-start gap-3">
                 <div class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-lg flex-shrink-0">🤖</div>
                 <div class="space-y-2 w-full">
                   <div class="bg-gray-100 rounded-lg rounded-tl-none p-2.5 text-xs text-gray-600">
                     "사장님이 30분 일찍 오라고 하는데, 이거 근무시간인가요?"
                   </div>
                   <div class="bg-brand-50 rounded-lg rounded-tr-none p-2.5 text-xs text-brand-800 font-medium">
                     네, 사용자의 지휘·감독 하에 있는 대기시간은 근로시간에 포함됩니다.
                   </div>
                 </div>
               </div>
             </div>

             <!-- Card 3: Resume/Docs -->
             <div class="bg-white/95 backdrop-blur-md rounded-2xl shadow-xl p-5 border border-white/50 transform translate-x-2 hover:translate-x-0 transition-transform duration-500">
               <div class="flex items-center justify-between mb-2">
                 <div class="flex items-center gap-2">
                    <span class="text-lg">📄</span>
                    <span class="text-sm font-bold text-gray-900">알바 이력서 생성</span>
                 </div>
                 <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
               </div>
               <div class="flex gap-2 mt-2">
                 <span class="text-[10px] bg-gray-100 px-2 py-1 rounded text-gray-500">#편의점 6개월</span>
                 <span class="text-[10px] bg-gray-100 px-2 py-1 rounded text-gray-500">#성실함</span>
                 <span class="text-[10px] bg-gray-100 px-2 py-1 rounded text-gray-500">#포스기능통</span>
               </div>
             </div>

           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
const router = useRouter();
</script>
