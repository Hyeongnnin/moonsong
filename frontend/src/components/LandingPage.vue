<template>
  <div class="min-h-screen bg-white">
    <!-- Hero Section -->
    <section class="pt-24 pb-16 bg-gradient-to-b from-blue-50 to-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid md:grid-cols-2 gap-12 items-center">
          <div class="space-y-6">
            <div class="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
              AI 설문으로 3분만에 근로현장 점검
            </div>
            <h1 class="text-4xl sm:text-5xl leading-tight text-gray-900">
              <span class="text-blue-600">근로 권리</span>를<br />
              쉽고 정확하게 진단받으세요
            </h1>
            <p class="text-gray-600 text-lg">
              복잡한 법률 상담 없이, AI 설문만으로<br />
              사업장의 노동법 준수 여부를 진단하고 전문가를 매칭받을 수 있어요
            </p>
            <div class="flex flex-wrap gap-4">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 rounded-full bg-blue-600 px-8 py-3 text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700"
                @click="navigateTo('rights-check')"
              >
                내 권리 알아보기
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m-7-7 7 7-7 7" />
                </svg>
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-full border border-gray-300 px-8 py-3 text-gray-800 transition hover:bg-gray-50"
                @click="scrollToSection('features')"
              >
                서비스 소개
              </button>
            </div>
            <div class="flex items-center gap-8 pt-4 text-base">
              <div>
                <div class="text-blue-600 font-semibold text-xl">12,567명</div>
                <div class="text-gray-500">누적 진단</div>
              </div>
              <div class="w-px h-12 bg-gray-200"></div>
              <div>
                <div class="text-blue-600 font-semibold text-xl">500+ 전문가</div>
                <div class="text-gray-500">노무사 네트워크</div>
              </div>
            </div>
          </div>
          <div class="relative">
            <div class="rounded-2xl overflow-hidden shadow-2xl">
              <img
                :src="heroImageSrc"
                alt="앱 미리보기"
                class="w-full h-auto object-cover"
                loading="lazy"
                @error="onHeroImageError"
              />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl mb-4 font-semibold text-gray-900">왜 노타브일까요?</h2>
          <p class="text-gray-600 text-lg">복잡한 노동법률, 이제는 쉽고 정확하게</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <article
            v-for="feature in features"
            :key="feature.title"
            class="p-8 rounded-2xl border border-gray-200 hover:shadow-lg transition-shadow"
          >
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
              <svg
                v-if="feature.icon === 'clock'"
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 text-blue-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M12 7v5l3 2" />
              </svg>
              <svg
                v-else-if="feature.icon === 'shield'"
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 text-blue-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M12 22s8-4 8-10V5L12 2 4 5v7c0 6 8 10 8 10z" />
                <path d="m9 12 2 2 4-4" />
              </svg>
              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6 text-blue-600"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <rect x="7" y="2" width="10" height="20" rx="2" ry="2" />
                <path d="M11 18h2" />
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-4 text-gray-900">{{ feature.title }}</h3>
            <p class="text-gray-600 leading-relaxed">{{ feature.description }}</p>
          </article>
        </div>
      </div>
    </section>

    <!-- How it works Section -->
    <section id="howto" class="py-20 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl mb-4 font-semibold text-gray-900">이용 방법</h2>
          <p class="text-gray-600 text-lg">간단한 3단계로 근로 권리를 지켜보세요</p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <article v-for="(step, index) in steps" :key="step.title" class="text-center">
            <div class="w-16 h-16 bg-blue-600 text-white text-2xl font-semibold rounded-full flex items-center justify-center mx-auto mb-6">
              {{ index + 1 }}
            </div>
            <h3 class="text-xl font-semibold mb-3 text-gray-900">{{ step.title }}</h3>
            <p class="text-gray-600 leading-relaxed" v-html="step.description"></p>
          </article>
        </div>
      </div>
    </section>

    <!-- Reviews Section -->
    <section id="reviews" class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl mb-4 font-semibold text-gray-900">이용자 후기</h2>
          <p class="text-gray-600 text-lg">1만 2천 명이 경험한 근로현장 법률진단 서비스</p>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <article v-for="review in reviews" :key="review.name" class="p-6 rounded-2xl border border-gray-200">
            <div class="flex items-center gap-3 mb-4">
              <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-semibold text-lg">
                {{ review.name.charAt(0) }}
              </div>
              <div>
                <div class="text-gray-900 font-semibold">{{ review.name }}</div>
                <div class="text-blue-600 text-sm">{{ review.job }}</div>
              </div>
            </div>
            <p class="text-gray-600 leading-relaxed">{{ review.review }}</p>
            <div class="flex gap-1 mt-4 text-yellow-400">
              <span v-for="star in 5" :key="`${review.name}-${star}`">★</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-gradient-to-r from-blue-600 to-blue-700 text-white text-center">
      <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 class="text-4xl mb-6 font-semibold">지금 바로 시작하세요</h2>
        <p class="mb-8 opacity-90 text-lg">
          근로현장의 법률 문제, 단 3분만에 진단하고 해결하세요
        </p>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-2 rounded-full bg-white text-blue-600 px-8 py-3 font-semibold transition hover:bg-gray-100"
          @click="navigateTo('rights-check')"
        >
          무료로 진단 받기
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14m-7-7 7 7-7 7" />
          </svg>
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-gray-400 py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid md:grid-cols-4 gap-8">
          <div>
            <h3 class="text-white text-xl font-semibold mb-4">노타브</h3>
            <p>청년을 위한 근로현장 법률진단 서비스</p>
          </div>
          <div>
            <h4 class="text-white font-semibold mb-4">서비스</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white transition">AI 법률 진단</a></li>
              <li><a href="#" class="hover:text-white transition">진단 보고서</a></li>
              <li><a href="#" class="hover:text-white transition">노무사 매칭</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-white font-semibold mb-4">고객지원</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white transition">자주 묻는 질문</a></li>
              <li><a href="#" class="hover:text-white transition">공지사항</a></li>
              <li><a href="#" class="hover:text-white transition">1:1 문의</a></li>
            </ul>
          </div>
          <div>
            <h4 class="text-white font-semibold mb-4">정보</h4>
            <ul class="space-y-2">
              <li><a href="#" class="hover:text-white transition">회사 소개</a></li>
              <li><a href="#" class="hover:text-white transition">이용약관</a></li>
              <li><a href="#" class="hover:text-white transition">개인정보처리방침</a></li>
            </ul>
          </div>
        </div>
        <div class="border-t border-gray-800 mt-12 pt-8 text-center text-sm">
          <p>&copy; 2025 노타브. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

type PageKey = 'landing' | 'login' | 'signup' | 'personal-signup' | 'lawyer-signup' | 'rights-check'

const router = useRouter()

const features = [
  {
    icon: 'clock',
    title: 'AI로 3분 진단',
    description: '복잡한 법률 용어 없이 간단한 AI 설문만으로 사업장의 노동법 준수 여부를 정확하게 진단할 수 있어요',
  },
  {
    icon: 'shield',
    title: '전문 보고서 제공',
    description: '진단 결과를 바탕으로 구체적인 법률 위반 사항과 개선 방안을 담은 보고서를 제공합니다',
  },
  {
    icon: 'phone',
    title: '전문 노무사 매칭',
    description: '필요시 경험 많은 노무사를 즉시 매칭해드려 구체적인 법률 상담과 문제 해결을 지원합니다',
  },
] as const

const steps = [
  {
    title: 'AI 설문 진단',
    description: '간단한 질문에 답하면<br />AI가 사업장을 정밀 진단합니다',
  },
  {
    title: '진단 보고서 확인',
    description: '노동법 위반 사항과<br />개선 방안을 담은 보고서를 받아보세요',
  },
  {
    title: '전문가 매칭',
    description: '필요시 전문 노무사와<br />1:1 상담을 진행하세요',
  },
] as const

const reviews = [
  { name: '김**', job: '카페 아르바이트', review: '급여 체불 문제를 해결할 수 있었어요. 노무사님과 상담도 도움이 됐습니다!' },
  { name: '이**', job: '편의점 알바', review: '법률 용어 몰라도 설문만 하면 되니까 너무 편했어요. 제 권리를 알게 됐어요.' },
  { name: '박**', job: '배달 라이더', review: '주휴수당 못 받고 있었는데 진단 받고 바로 해결했습니다. 추천해요!' },
] as const

const heroImagePrimary =
  'https://images.unsplash.com/photo-1605108222700-0d605d9ebafe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2JpbGUlMjBwaG9uZSUyMGFwcHxlbnwxfHx8fDE3NjMwNTA3MDF8MA&ixlib=rb-4.1.0&q=80&w=1080'
const heroImageFallback = 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=1080&q=80'
const heroImageSrc = ref(heroImagePrimary)

const onHeroImageError = () => {
  heroImageSrc.value = heroImageFallback
}

const navigateTo = (page: PageKey) => {
  if (page === 'landing') {
    router.push('/')
    return
  }

  const routeMap: Record<Exclude<PageKey, 'landing'>, string> = {
    login: '/login',
    signup: '/signup',
    'personal-signup': '/signup/personal',
    'lawyer-signup': '/signup/lawyer',
    'rights-check': '/rights-check',
  }

  router.push(routeMap[page])
}

const scrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' })
  }
}
</script>
