#average price per item
library(data.table)
library(ggplot2)

read<-function(tmax=5) {
  file="/Users/davej/data/AVSC/trainHistory_with_MF_features.csv"
  data=data.table(read.csv(file,as.is=T))
  data[,Repeat.Trips:=ifelse(repeattrips<tmax,repeattrips,tmax)]
  return(data)
  
  dat=data[,list(N=.N,score.mean=mean(score,na.rm=T,trim=0.01),),by=repeattrips]
  dat=dat[N>10,]
  dat[,trips:=repeattrips+1]
  dat[,scaled.trips:=log(1.0+trips)/log(2)]
  dat[,score.mean.err:=score.sigma/sqrt(N)]
  return(data)
}

doplot<-function(data){
  p<-ggplot(data,aes(scaled.trips,score.mean))+geom_point(size=3)
  p=p+geom_errorbar(aes(ymin=score.mean-score.mean.err,ymax=score.mean+score.mean.err))
  #p=p+geom_errorbar(aes(ymin=score.mean-score.sigma,ymax=score.mean+score.sigma))
  print(p)
}

doplot2<-function(data){
  p<-ggplot(data,aes(score,fill=factor(Repeat.Trips)))+geom_density(alpha=0.1)
  p=p+xlab("MF Score")+xlim(-0.2,0.8)
  print(p)
}

prep<-function(data){
  d.yes=data[repeater=='t',]
  d.no=data[repeater=='f',]
  d.yes=d.yes[sample(nrow(d.yes)),]
  d.no=d.no[sample(nrow(d.no)),]
  row.max=min(nrow(d.yes),nrow(d.no))
  d.yes=d.yes[1:row.max,]
  d.no=d.no[1:row.max,]
  d=rbind(d.yes,d.no)
  d=d[sample(nrow(d)),]
  return(d)
}


