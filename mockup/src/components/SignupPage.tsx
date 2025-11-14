import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card } from "./ui/card";
import { Separator } from "./ui/separator";
import { Checkbox } from "./ui/checkbox";
import { useState } from "react";
import { Check } from "lucide-react";

interface SignupPageProps {
  onNavigate: (page: 'landing' | 'login' | 'signup') => void;
}

export function SignupPage({ onNavigate }: SignupPageProps) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    phone: "",
  });

  const [agreements, setAgreements] = useState({
    terms: false,
    privacy: false,
    marketing: false,
  });

  const allRequired = agreements.terms && agreements.privacy;

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAgreement = (field: string, value: boolean) => {
    setAgreements(prev => ({ ...prev, [field]: value }));
  };

  const handleAgreeAll = () => {
    const newValue = !allRequired;
    setAgreements({
      terms: newValue,
      privacy: newValue,
      marketing: newValue,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!allRequired) {
      alert("필수 약관에 동의해주세요.");
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      alert("비밀번호가 일치하지 않습니다.");
      return;
    }
    console.log("회원가입:", formData, agreements);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-24">
      <Card className="w-full max-w-2xl p-8 bg-white">
        <div className="text-center mb-8">
          <h1 className="text-3xl mb-2">회원가입</h1>
          <p className="text-gray-600">
            3분이면 가입 완료! 지금 바로 근로 권리를 진단받으세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 소셜 회원가입 */}
          <div className="space-y-3">
            <Button
              type="button"
              variant="outline"
              className="w-full"
              size="lg"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="#03C75A" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 0 0-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
              </svg>
              카카오로 3초만에 시작하기
            </Button>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              size="lg"
            >
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              구글로 시작하기
            </Button>
          </div>

          <div className="relative">
            <Separator className="my-6" />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-4 text-gray-500">
              또는 이메일로 가입
            </span>
          </div>

          {/* 이메일 회원가입 */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">이름 *</Label>
              <Input
                id="name"
                type="text"
                placeholder="홍길동"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">휴대폰 번호 *</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="010-1234-5678"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">이메일 *</Label>
            <Input
              id="email"
              type="email"
              placeholder="example@email.com"
              value={formData.email}
              onChange={(e) => handleChange('email', e.target.value)}
              required
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호 *</Label>
              <Input
                id="password"
                type="password"
                placeholder="8자 이상 입력"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">비밀번호 확인 *</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="비밀번호 재입력"
                value={formData.confirmPassword}
                onChange={(e) => handleChange('confirmPassword', e.target.value)}
                required
                minLength={8}
              />
            </div>
          </div>

          {/* 약관 동의 */}
          <div className="border rounded-lg p-6 space-y-4 bg-gray-50">
            <div className="flex items-center gap-3 pb-3 border-b">
              <Checkbox
                id="agreeAll"
                checked={allRequired && agreements.marketing}
                onCheckedChange={handleAgreeAll}
              />
              <label htmlFor="agreeAll" className="cursor-pointer select-none">
                전체 동의
              </label>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Checkbox
                    id="terms"
                    checked={agreements.terms}
                    onCheckedChange={(checked) => handleAgreement('terms', checked as boolean)}
                  />
                  <label htmlFor="terms" className="cursor-pointer select-none">
                    <span className="text-blue-600">[필수]</span> 이용약관 동의
                  </label>
                </div>
                <button type="button" className="text-gray-500 hover:text-gray-700">
                  보기
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Checkbox
                    id="privacy"
                    checked={agreements.privacy}
                    onCheckedChange={(checked) => handleAgreement('privacy', checked as boolean)}
                  />
                  <label htmlFor="privacy" className="cursor-pointer select-none">
                    <span className="text-blue-600">[필수]</span> 개인정보 처리방침 동의
                  </label>
                </div>
                <button type="button" className="text-gray-500 hover:text-gray-700">
                  보기
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Checkbox
                    id="marketing"
                    checked={agreements.marketing}
                    onCheckedChange={(checked) => handleAgreement('marketing', checked as boolean)}
                  />
                  <label htmlFor="marketing" className="cursor-pointer select-none">
                    <span className="text-gray-500">[선택]</span> 마케팅 정보 수신 동의
                  </label>
                </div>
                <button type="button" className="text-gray-500 hover:text-gray-700">
                  보기
                </button>
              </div>
            </div>
          </div>

          <Button 
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
            size="lg"
            disabled={!allRequired}
          >
            회원가입 완료
          </Button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-600">
            이미 계정이 있으신가요?{" "}
            <button
              onClick={() => onNavigate('login')}
              className="text-blue-600 hover:underline"
            >
              로그인
            </button>
          </p>
        </div>
      </Card>
    </div>
  );
}