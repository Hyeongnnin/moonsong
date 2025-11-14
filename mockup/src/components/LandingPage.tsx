import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Check, ArrowRight, Clock, Shield, Smartphone } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface LandingPageProps {
  onNavigate: (page: 'landing' | 'login' | 'signup') => void;
}

export function LandingPage({ onNavigate }: LandingPageProps) {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="pt-24 pb-16 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full">
                AI 설문으로 3분만에 근로현장 점검
              </div>
              <h1 className="text-5xl">
                <span className="text-blue-600">근로 권리</span>를<br />
                쉽고 정확하게 진단받으세요
              </h1>
              <p className="text-gray-600">
                복잡한 법률 상담 없이, AI 설문만으로<br />
                사업장의 노동법 준수 여부를 진단하고 전문가를 매칭받을 수 있어요
              </p>
              <div className="flex gap-4">
                <Button 
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8"
                  onClick={() => onNavigate('signup')}
                >
                  내 권리 알아보기
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                <Button 
                  size="lg"
                  variant="outline"
                >
                  서비스 소개
                </Button>
              </div>
              <div className="flex items-center gap-8 pt-4">
                <div>
                  <div className="text-blue-600">12,567명</div>
                  <div className="text-gray-500">누적 진단</div>
                </div>
                <div className="w-px h-12 bg-gray-200"></div>
                <div>
                  <div className="text-blue-600">500+ 전문가</div>
                  <div className="text-gray-500">노무사 네트워크</div>
                </div>
              </div>
            </div>
            <div className="relative">
              <div className="rounded-2xl overflow-hidden shadow-2xl">
                <ImageWithFallback 
                  src="https://images.unsplash.com/photo-1605108222700-0d605d9ebafe?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2JpbGUlMjBwaG9uZSUyMGFwcHxlbnwxfHx8fDE3NjMwNTA3MDF8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                  alt="앱 미리보기"
                  className="w-full h-auto"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl mb-4">왜 노타브일까요?</h2>
            <p className="text-gray-600">
              복잡한 노동법률, 이제는 쉽고 정확하게
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="p-8 hover:shadow-lg transition-shadow border-gray-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                <Clock className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="mb-4">AI로 3분 진단</h3>
              <p className="text-gray-600">
                복잡한 법률 용어 없이 간단한 AI 설문만으로 사업장의 노동법 준수 여부를 정확하게 진단할 수 있어요
              </p>
            </Card>

            <Card className="p-8 hover:shadow-lg transition-shadow border-gray-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                <Shield className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="mb-4">전문 보고서 제공</h3>
              <p className="text-gray-600">
                진단 결과를 바탕으로 구체적인 법률 위반 사항과 개선 방안을 담은 보고서를 제공합니다
              </p>
            </Card>

            <Card className="p-8 hover:shadow-lg transition-shadow border-gray-200">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-6">
                <Smartphone className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="mb-4">전문 노무사 매칭</h3>
              <p className="text-gray-600">
                필요시 경험 많은 노무사를 즉시 매칭해드려 구체적인 법률 상담과 문제 해결을 지원합니다
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* How it works Section */}
      <section id="howto" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl mb-4">이용 방법</h2>
            <p className="text-gray-600">
              간단한 3단계로 근로 권리를 지켜보세요
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6">
                1
              </div>
              <h3 className="mb-3">AI 설문 진단</h3>
              <p className="text-gray-600">
                간단한 질문에 답하면<br />AI가 사업장을 정밀 진단합니다
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6">
                2
              </div>
              <h3 className="mb-3">진단 보고서 확인</h3>
              <p className="text-gray-600">
                노동법 위반 사항과<br />개선 방안을 담은 보고서를 받아보세요
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto mb-6">
                3
              </div>
              <h3 className="mb-3">전문가 매칭</h3>
              <p className="text-gray-600">
                필요시 전문 노무사와<br />1:1 상담을 진행하세요
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Reviews Section */}
      <section id="reviews" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl mb-4">이용자 후기</h2>
            <p className="text-gray-600">
              1만 2천 명이 경험한 근로현장 법률진단 서비스
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { name: "김**", job: "카페 아르바이트", review: "급여 체불 문제를 해결할 수 있었어요. 노무사님과 상담도 도움이 됐습니다!" },
              { name: "이**", job: "편의점 알바", review: "법률 용어 몰라도 설문만 하면 되니까 너무 편했어요. 제 권리를 알게 됐어요." },
              { name: "박**", job: "배달 라이더", review: "주휴수당 못 받고 있었는데 진단 받고 바로 해결했습니다. 추천해요!" }
            ].map((review, i) => (
              <Card key={i} className="p-6 border-gray-200">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600">{review.name[0]}</span>
                  </div>
                  <div>
                    <div>{review.name}</div>
                    <div className="text-blue-600">{review.job}</div>
                  </div>
                </div>
                <p className="text-gray-600">{review.review}</p>
                <div className="flex gap-1 mt-4">
                  {[1,2,3,4,5].map((star) => (
                    <span key={star} className="text-yellow-400">★</span>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-blue-700 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl mb-6">지금 바로 시작하세요</h2>
          <p className="mb-8 opacity-90">
            근로현장의 법률 문제, 단 3분만에 진단하고 해결하세요
          </p>
          <Button 
            size="lg"
            className="bg-white text-blue-600 hover:bg-gray-100 px-8"
            onClick={() => onNavigate('signup')}
          >
            무료로 진단 받기
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <h3 className="text-white mb-4">노타브</h3>
              <p>
                청년을 위한 근로현장 법률진단 서비스
              </p>
            </div>
            <div>
              <h4 className="text-white mb-4">서비스</h4>
              <ul className="space-y-2">
                <li><a href="#" className="hover:text-white">AI 법률 진단</a></li>
                <li><a href="#" className="hover:text-white">진단 보고서</a></li>
                <li><a href="#" className="hover:text-white">노무사 매칭</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white mb-4">고객지원</h4>
              <ul className="space-y-2">
                <li><a href="#" className="hover:text-white">자주 묻는 질문</a></li>
                <li><a href="#" className="hover:text-white">공지사항</a></li>
                <li><a href="#" className="hover:text-white">1:1 문의</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white mb-4">정보</h4>
              <ul className="space-y-2">
                <li><a href="#" className="hover:text-white">회사 소개</a></li>
                <li><a href="#" className="hover:text-white">이용약관</a></li>
                <li><a href="#" className="hover:text-white">개인정보처리방침</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-center">
            <p>&copy; 2025 노타브. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}