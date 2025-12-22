<template>
  <section class="flex flex-col h-full">
    <h2 class="text-2xl font-semibold mb-4 px-2">AI 노무 상담</h2>
    
    <!-- Chat Area -->
    <div class="flex-1 overflow-y-auto p-4 bg-gray-50 rounded-lg border border-gray-200 mb-4 h-[500px]" ref="chatContainer">
      <div v-if="messages.length === 0" class="text-center text-gray-500 mt-20">
        <div class="text-4xl mb-4">🤖</div>
        <p class="text-lg font-medium text-gray-700">무엇이든 물어보세요!</p>
        <p class="text-sm mt-2 text-gray-400">
          "내 시급이 얼마야?"<br>
          "최근 3개월 급여 내역 알려줘"<br>
          "주휴수당은 어떻게 계산해?"
        </p>
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" class="mb-4">
        <!-- User Message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="bg-brand-600 text-white px-4 py-2.5 rounded-2xl rounded-tr-none max-w-[85%] whitespace-pre-wrap shadow-sm">
            {{ msg.content }}
          </div>
        </div>
        <!-- AI Message -->
        <div v-else class="flex justify-start">
          <div class="flex flex-col max-w-[85%]">
            <div class="font-bold text-brand-600 text-xs mb-1 ml-1">AI 노무사</div>
            <div class="bg-white border border-gray-200 text-gray-800 px-4 py-2.5 rounded-2xl rounded-tl-none whitespace-pre-wrap shadow-sm leading-relaxed">
              {{ msg.content }}
            </div>
          </div>
        </div>
      </div>

      <!-- Loading Indicator -->
      <div v-if="isLoading" class="flex justify-start mb-4">
         <div class="bg-white border border-gray-200 text-gray-500 px-4 py-2 rounded-lg shadow-sm flex items-center gap-2">
            <div class="w-2 h-2 bg-brand-400 rounded-full animate-bounce"></div>
            <div class="w-2 h-2 bg-brand-400 rounded-full animate-bounce delay-100"></div>
            <div class="w-2 h-2 bg-brand-400 rounded-full animate-bounce delay-200"></div>
         </div>
      </div>
    </div>

    <!-- Input Area -->
    <div class="px-1 pb-1">
      <div class="flex gap-2">
        <input 
          v-model="userInput" 
          @keyup.enter="sendMessage"
          type="text" 
          class="flex-1 border border-gray-300 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all shadow-sm"
          placeholder="궁금한 내용을 입력하세요..." 
          :disabled="isLoading"
        />
        <button 
          @click="sendMessage" 
          :disabled="isLoading || !userInput.trim()"
          class="bg-brand-600 text-white px-6 py-2 rounded-xl hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors shadow-sm whitespace-nowrap"
        >
          전송
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import { aiConsult } from '../api';

interface Message {
  role: 'user' | 'ai';
  content: string;
}

const messages = ref<Message[]>([]);
const userInput = ref('');
const isLoading = ref(false);
const chatContainer = ref<HTMLElement | null>(null);

async function sendMessage() {
  const text = userInput.value.trim();
  if (!text) return;

  // Add user message
  messages.value.push({ role: 'user', content: text });
  userInput.value = '';
  isLoading.value = true;
  forceScroll();

  try {
    const res = await aiConsult(text);
    messages.value.push({ role: 'ai', content: res.answer });
  } catch (err: any) {
    console.error(err);
    const errMsg = err.response?.data?.detail || "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.";
    messages.value.push({ role: 'ai', content: `[오류] ${errMsg}` });
  } finally {
    isLoading.value = false;
    forceScroll();
  }
}

function forceScroll() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
      setTimeout(() => {
          if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
      }, 100);
    }
  });
}
</script>

<style scoped>
/* 커스텀 스크롤바 */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #f1f1f1; 
}
::-webkit-scrollbar-thumb {
  background: #d1d5db; 
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #9ca3af; 
}
</style>
